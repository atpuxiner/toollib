import { defaultTheme, defineUserConfig } from 'vuepress'

export default defineUserConfig({
  base: '/',
  head: [['link', { rel: 'icon', href: '/favicon.ico' }]],

  locales: {
    '/': {
      lang: 'zh-CN',
      title: 'toollib',
      description: '描述',
    },
    '/en/': {
      lang: 'en-US',
      title: 'toollib',
      description: 'description',
    },
  },

  theme: defaultTheme({
    logo: '/favicon.ico',

    locales: {
      '/': {
        lang: 'zh-CN',
        selectLanguageName: '简体中文',
        navbar: [
          { text: '指南', link: '/zh/guide/introduce' }
        ],
        sidebar: {
          '/zh/guide/': [{
            text: '指南',
            children: [
              {
                text: '介绍',
                link: '/zh/guide/introduce'
              },
              {
                text: '安装',
                link: '/zh/guide/install'
              },
              {
                text: '使用',
                link: '/zh/guide/usage'
              }
            ]
          }]
        }
      },
      '/en/': {
        lang: 'en',
        selectLanguageName: 'English',
        navbar: [
          { text: 'guide', link: '/en/guide/introduce' }
        ],
        sidebar: {
          '/en/guide/': [{
            text: 'guide',
            children: [
              {
                text: 'introduce',
                link: '/en/guide/introduce'
              },
              {
                text: 'install',
                link: '/en/guide/install'
              },
              {
                text: 'usage',
                link: '/en/guide/usage'
              }
            ]
          }]
        }
      }
    }
  })
})