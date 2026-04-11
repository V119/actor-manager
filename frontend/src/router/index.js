import { createRouter, createWebHistory } from 'vue-router'
import EditPortrait from '../views/EditPortrait.vue'
import StyleLab from '../views/StyleLab.vue'
import ProtocolManagement from '../views/ProtocolManagement.vue'
import DiscoverySquare from '../views/DiscoverySquare.vue'
import ActorProfile from '../views/ActorProfile.vue'

const routes = [
  { path: '/', redirect: '/discovery' },
  { path: '/edit-portrait', name: 'EditPortrait', component: EditPortrait },
  { path: '/style-lab', name: 'StyleLab', component: StyleLab },
  { path: '/protocols', name: 'ProtocolManagement', component: ProtocolManagement },
  { path: '/discovery', name: 'DiscoverySquare', component: DiscoverySquare },
  { path: '/actor/:id', name: 'ActorProfile', component: ActorProfile, props: true }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
