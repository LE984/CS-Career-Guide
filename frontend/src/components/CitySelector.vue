<template>
  <div class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" v-if="show">
    <div class="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl transform transition-all">
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-800 mb-2">选择你的城市</h2>
        <p class="text-gray-500">{{ subtitle }}</p>
      </div>

      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="city in hotCities"
            :key="city.name"
            @click="selectCity(city)"
            class="flex items-center gap-3 p-4 bg-gray-50 hover:bg-blue-50 rounded-xl transition-all hover:shadow-md"
          >
            <div class="w-10 h-10 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-lg flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
            </div>
            <div class="text-left">
              <div class="font-semibold text-gray-800">{{ city.name }}</div>
              <div class="text-xs text-gray-500">{{ city.jobs }} 个职位</div>
            </div>
          </button>
        </div>
      </div>

      <div class="mt-6 pt-6 border-t border-gray-100">
        <button
          v-if="!locationAttempted || locationError"
          @click="getLocation"
          :disabled="locationLoading"
          class="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-cyan-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <svg v-if="locationLoading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
          </svg>
          {{ locationLoading ? '获取位置中...' : '使用当前位置' }}
        </button>
        <p v-if="locationError" class="text-center text-red-500 text-sm mt-2">{{ locationError }}</p>
      </div>

      <button
        @click="$emit('close')"
        class="mt-4 w-full py-2 text-gray-500 hover:text-gray-700 transition-colors text-sm"
      >
        稍后选择
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { GEOCODING_URL } from '@/config'

const props = defineProps({
  show: Boolean,
  subtitle: {
    type: String,
    default: '选择城市后将为您推荐相关职位'
  },
  hotCities: {
    type: Array,
    default: () => [
      { name: '长沙', pinyin: 'changsha', jobs: 120 },
      { name: '北京', pinyin: 'beijing', jobs: 350 },
      { name: '上海', pinyin: 'shanghai', jobs: 420 },
      { name: '深圳', pinyin: 'shenzhen', jobs: 280 },
      { name: '广州', pinyin: 'guangzhou', jobs: 210 },
      { name: '杭州', pinyin: 'hangzhou', jobs: 180 },
      { name: '成都', pinyin: 'chengdu', jobs: 150 },
      { name: '武汉', pinyin: 'wuhan', jobs: 130 }
    ]
  }
})

const emit = defineEmits(['select', 'close'])

const locationLoading = ref(false)
const locationError = ref('')
const locationAttempted = ref(false)

const getLocation = async () => {
  if (!GEOCODING_URL) {
    locationError.value = '未配置城市定位服务，请手动选择城市'
    return
  }
  if (!('geolocation' in navigator)) {
    locationError.value = '您的浏览器不支持地理定位'
    return
  }

  locationLoading.value = true
  locationError.value = ''

  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        resolve,
        reject,
        {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 300000
        }
      )
    })

    const { latitude, longitude } = position.coords
    const city = await reverseGeocode(latitude, longitude)
    
    if (city) {
      emit('select', { name: city, latitude, longitude })
    } else {
      locationError.value = '无法获取您所在的城市'
    }
  } catch (error) {
    console.error('获取位置失败:', error)
    if (error.code === error.PERMISSION_DENIED) {
      locationError.value = '您拒绝了位置权限，请手动选择城市'
    } else if (error.code === error.TIMEOUT) {
      locationError.value = '获取位置超时，请重试'
    } else {
      locationError.value = '获取位置失败，请手动选择城市'
    }
  } finally {
    locationLoading.value = false
    locationAttempted.value = true
  }
}

const reverseGeocode = async (latitude, longitude) => {
  try {
    const endpoint = new URL(GEOCODING_URL, window.location.origin)
    endpoint.searchParams.set('q', `${latitude},${longitude}`)
    endpoint.searchParams.set('language', 'zh-CN')
    const response = await fetch(endpoint)
    const data = await response.json()
    
    if (data.results && data.results.length > 0) {
      const components = data.results[0].components
      if (components.city) {
        return components.city
      } else if (components.town) {
        return components.town
      } else if (components.state) {
        return components.state
      }
    }
    return null
  } catch (error) {
    console.error('逆地理编码失败:', error)
    return null
  }
}

const selectCity = (city) => {
  emit('select', { name: city.name, pinyin: city.pinyin })
}

onMounted(() => {
  if (props.show) {
    getLocation()
  }
})
</script>
