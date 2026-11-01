"""Export verified images and publish those exact archives in the gated CI job."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

COMPONENTS = ('backend', 'frontend')
DIGEST = r'sha256:[0-9a-f]{64}'


def source_image(component, commit):
    if component not in COMPONENTS or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('A supported component and full commit SHA are required.')
    return f'cs-career-guide-{component}:sha-{commit[:7]}'


def coordinates(registry, namespace, commit, extra_tag=''):
    source_image('backend', commit)
    if not registry or not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]+)?', registry):
        raise ValueError('ACR_REGISTRY must be a registry hostname without a URL scheme or path.')
    if not namespace or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', namespace):
        raise ValueError('ACR_NAMESPACE must contain lowercase letters, digits or hyphens.')
    if extra_tag and not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._-]{0,127}', extra_tag):
        raise ValueError('extra_tag must be a valid Docker tag.')
    return {name: f'{registry}/{namespace}/cs-career-guide-{name}' for name in COMPONENTS}


def docker(*arguments):
    result = subprocess.run(['docker', *arguments], capture_output=True, text=True, check=False)
    if result.returncode:
        # Do not echo registry configuration, credentials or arbitrary CLI output.
        raise RuntimeError(f'Docker {arguments[0]} failed with exit code {result.returncode}.')
    return result.stdout


def inspect_image(image):
    images = json.loads(docker('image', 'inspect', image))
    if len(images) != 1:
        raise RuntimeError('Expected exactly one inspected image.')
    image = images[0]
    if image.get('Os') != 'linux' or image.get('Architecture') != 'amd64':
        raise RuntimeError('Only the validated linux/amd64 image may be released.')
    if not re.fullmatch(DIGEST, image.get('Id', '')):
        raise RuntimeError('The validated image ID is missing or malformed.')
    return image['Id']


def export_image(directory, component, commit):
    source = source_image(component, commit)
    image_id = inspect_image(source)
    directory.mkdir(parents=True, exist_ok=True)
    docker('save', '--output', str(directory / f'{component}-image.tar'), source)
    metadata = {'component': component, 'commit': commit, 'source_image': source,
                'image_id': image_id, 'platform': 'linux/amd64'}
    (directory / f'{component}-image.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f'Exported verified {component} image and identity metadata.', flush=True)


def load_verified_images(directory, commit, components=COMPONENTS):
    verified = {}
    # Reject either archive's metadata before loading or tagging anything.
    if not components or len(set(components)) != len(components) or set(components) - set(COMPONENTS):
        raise ValueError('Select supported release components.')
    for component in components:
        metadata = json.loads((directory / f'{component}-image.json').read_text(encoding='utf-8'))
        if (metadata.get('component') != component or metadata.get('commit') != commit
                or metadata.get('source_image') != source_image(component, commit)
                or metadata.get('platform') != 'linux/amd64'
                or not re.fullmatch(DIGEST, metadata.get('image_id', ''))):
            raise RuntimeError('Image artifact identity does not match the validated commit and platform.')
        if not (directory / f'{component}-image.tar').is_file():
            raise RuntimeError('The verified image archive is missing.')
        verified[component] = metadata
    for component, metadata in verified.items():
        docker('load', '--input', str(directory / f'{component}-image.tar'))
        if inspect_image(metadata['source_image']) != metadata['image_id']:
            raise RuntimeError('Loaded image ID differs from the validated artifact.')
    return verified


def push_digest(output):
    digests = set(re.findall(r'\bdigest:\s*(' + DIGEST + r')\b', output))
    if len(digests) != 1:
        raise RuntimeError('Docker push did not report one unambiguous manifest digest.')
    return digests.pop()


def write_release(output, summary, release):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(release, indent=2) + '\n', encoding='utf-8')
    title = 'Published verified images' if release['complete'] else 'Partial or failed image publication'
    lines = [f'## {title}', '', f"Commit: `{release['commit']}`",
             f"Compatibility evidence: `{release['compatibility']}`", '']
    for component, image in release['images'].items():
        if image.get('reference'):
            lines.append(f"- {component}: `{image['reference']}`")
    lines += ['', 'Roll back only the selected component using its recorded digest. Tags can be overwritten.',
              'A partial publication must not be treated as a completed release.', '']
    with summary.open('a', encoding='utf-8') as stream:
        stream.write('\n'.join(lines))


def publish_images(directory, registry, namespace, commit, extra_tag, output, summary, components=COMPONENTS,
                   compatibility='not-recorded'):
    if compatibility not in ('not-recorded', 'component-contracts', 'candidate-integration'):
        raise ValueError('Unsupported compatibility evidence scope.')
    repositories = coordinates(registry, namespace, commit, extra_tag)
    verified = load_verified_images(directory, commit, components)
    release = {'commit': commit, 'components': list(components), 'compatibility': compatibility,
               'complete': False, 'images': {
        component: {'repository': repositories[component], 'image_id': metadata['image_id'], 'tags': []}
        for component, metadata in verified.items()
    }}
    version_tags = list(dict.fromkeys([f'sha-{commit[:7]}'] + ([extra_tag] if extra_tag and extra_tag != 'latest' else [])))
    try:
        # Advance rolling tags only for the explicitly selected components.
        for tag in [*version_tags, 'latest']:
            for component, metadata in verified.items():
                reference = f'{repositories[component]}:{tag}'
                docker('tag', metadata['image_id'], reference)
                digest = push_digest(docker('push', reference))
                image = release['images'][component]
                if image.get('digest', digest) != digest:
                    raise RuntimeError('Published tags resolved to different manifest digests.')
                image.update(digest=digest, reference=f'{repositories[component]}@{digest}')
                image['tags'].append(tag)
                print(f'Published verified {component} tag {tag}.', flush=True)
        release['complete'] = True
    finally:
        write_release(output, summary, release)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    export = commands.add_parser('export')
    export.add_argument('--component', choices=COMPONENTS, required=True)
    export.add_argument('--commit', required=True)
    export.add_argument('--directory', type=Path, required=True)
    verify = commands.add_parser('verify')
    verify.add_argument('--commit', required=True)
    verify.add_argument('--directory', type=Path, required=True)
    verify.add_argument('--component', choices=COMPONENTS, action='append')
    for name in ('check-config', 'publish'):
        command = commands.add_parser(name)
        command.add_argument('--commit', required=True)
        command.add_argument('--extra-tag', default='')
        if name == 'publish':
            command.add_argument('--compatibility', choices=('not-recorded', 'component-contracts', 'candidate-integration'),
                                 default='not-recorded')
            command.add_argument('--component', choices=COMPONENTS, action='append')
            command.add_argument('--directory', type=Path, required=True)
            command.add_argument('--output', type=Path, required=True)
            command.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'export':
        export_image(args.directory, args.component, args.commit)
        return
    if args.command == 'verify':
        load_verified_images(args.directory, args.commit, args.component or COMPONENTS)
        print('Selected archives match the validated commit, image IDs and linux/amd64 platform.')
        return
    registry = os.getenv('ACR_REGISTRY', '')
    namespace = os.getenv('ACR_NAMESPACE', '')
    if args.command == 'check-config':
        coordinates(registry, namespace, args.commit, args.extra_tag)
        print('Registry coordinate configuration is valid.')
    else:
        publish_images(args.directory, registry, namespace, args.commit, args.extra_tag,
                       args.output, args.summary, args.component or COMPONENTS, args.compatibility)


if __name__ == '__main__':
    main()
