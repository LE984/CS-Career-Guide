// Original introductory study material. Local self-practice only: these IDs
// must never be sent to the formal catalog/session APIs.
export const defaultQuestionSets = [
  { id:'java', title:'Java 后端基础', description:'集合、对象约定与并发入门', questions:[
    { id:'java-equals', question:'为什么重写 equals 时通常也需要重写 hashCode？', key_points:['equals 判断相等的对象必须返回相同的 hashCode。','哈希集合先定位哈希桶，再使用 equals 判断相等。','不同对象可以产生相同哈希值，因此哈希相同不代表对象相等。'] },
    { id:'java-list', question:'ArrayList 与 LinkedList 各适合什么场景？', key_points:['ArrayList 基于动态数组，按索引访问通常为 O(1)。','LinkedList 基于双向链表，定位节点通常需要遍历。','已定位节点的链表插入删除成本较低，但需考虑定位、内存和缓存局部性，不能笼统认为链表总是更快。'] },
    { id:'java-thread', question:'synchronized 解决什么问题？为什么仍要控制锁的范围？', key_points:['同一监视器上的同步可实现互斥，并提供相应的可见性保证。','共享状态的相关访问需要遵守一致的同步策略。','锁范围过大会增加竞争；多锁顺序不一致可能造成死锁。'] },
  ]},
  { id:'python', title:'Python 开发基础', description:'数据结构、迭代与资源管理', questions:[
    { id:'python-list', question:'列表和元组有什么区别？元组中的内容一定不能改变吗？', key_points:['列表支持增删和元素赋值，元组不能替换自身的元素引用。','元组可以包含可变对象，这些对象的内部内容仍可能改变。','元组只有在其元素均可哈希时才可作为字典键。'] },
    { id:'python-generator', question:'生成器与一次性创建列表有什么区别？', key_points:['生成器按需产生值，不需要预先保存所有结果。','生成器通常只能顺序消费一次，耗尽后不自动重新开始。','延迟计算有助于处理大数据流，但不等于任意场景下都更快。'] },
    { id:'python-with', question:'用 with 打开文件有什么好处？', key_points:['上下文管理器通过进入和退出协议管理资源。','即使代码块发生异常，也会调用退出逻辑以执行资源清理。','文件关闭不意味着异常必然被吞掉；是否抑制异常取决于退出逻辑。'] },
  ]},
  { id:'frontend', title:'前端开发基础', description:'浏览器、异步请求与响应式界面', questions:[
    { id:'frontend-event', question:'浏览器中的任务与微任务如何影响执行顺序？', key_points:['同步代码先在当前任务中执行。','任务结束后通常会清空微任务队列，再进入后续任务或渲染机会。','持续加入微任务可能阻塞后续任务与渲染，不能认为每个任务之后一定立即绘制。'] },
    { id:'frontend-race', question:'搜索框连续发出多个请求，怎样避免旧结果覆盖新结果？', key_points:['为请求分配递增序号或身份，只接收当前请求的结果。','可以使用 AbortController 取消旧请求以减少无用工作。','取消本身不能替代结果身份检查，还应处理卸载、错误与加载状态。'] },
    { id:'frontend-key', question:'Vue 列表渲染为什么需要稳定的 key？', key_points:['key 帮助框架识别节点身份，正确复用或移动节点。','包含输入和局部状态的列表在重排时尤其需要稳定身份。','可重排列表通常应使用稳定业务 ID，而不是数组下标或每次渲染生成的随机值。'] },
  ]},
]
export const defaultQuestionSource = '项目自编 · 入门自练材料（非真实面经）'
