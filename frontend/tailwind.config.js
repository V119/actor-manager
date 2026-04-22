const ink = {
  50: '#f4f8f5',
  100: '#dce7df',
  200: '#bdcdc2',
  300: '#9caea1',
  400: '#788d81',
  500: '#5d7067',
  600: '#46564f',
  700: '#33403b',
  800: '#202b27',
  900: '#121a17',
  950: '#08110e'
}

const moss = {
  50: '#f3faf5',
  100: '#daece0',
  200: '#bad7c3',
  300: '#94bfa3',
  400: '#6fa98a',
  500: '#4f876b',
  600: '#3f6b56',
  700: '#315244',
  800: '#233b31',
  900: '#172722',
  950: '#0b1512'
}

const sage = {
  50: '#f5faf7',
  100: '#dfece5',
  200: '#c5d9ce',
  300: '#a2bfaf',
  400: '#7ca289',
  500: '#5d7d68',
  600: '#486353',
  700: '#394e42',
  800: '#293932',
  900: '#18231f',
  950: '#0c1411'
}

const brass = {
  50: '#fbf6ee',
  100: '#efe2cc',
  200: '#ddc6a0',
  300: '#c9a170',
  400: '#b1834d',
  500: '#906536',
  600: '#724f2b',
  700: '#583e22',
  800: '#402e1a',
  900: '#2e2013',
  950: '#1b130b'
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  theme: {
    extend: {
      colors: {
        ink,
        moss,
        sage,
        brass,
        sky: moss,
        emerald: sage,
        amber: brass,
        slate: ink,
        background: ink[950],
        'surface-bright': '#193029',
        surface: '#10201b',
        'on-tertiary-container': '#f4e2c7',
        'outline-variant': '#2b3f37',
        'error-container': '#3a1718',
        'surface-container-lowest': ink[950],
        'primary-fixed-dim': moss[400],
        'on-primary': '#07100d',
        'on-secondary-container': '#dce9e1',
        'on-secondary-fixed-variant': '#3a5f4d',
        'surface-container-low': '#13231d',
        'on-tertiary-fixed': '#24170d',
        'surface-container': '#162922',
        'on-error-container': '#ffd2d1',
        'secondary-fixed': sage[200],
        'tertiary-container': '#4d3822',
        'surface-container-highest': '#243b32',
        'secondary-fixed-dim': sage[300],
        'on-tertiary-fixed-variant': '#7e5f3d',
        'on-secondary-fixed': '#0b1713',
        'primary-fixed': moss[200],
        outline: '#597264',
        'on-secondary': '#08110e',
        tertiary: brass[300],
        'surface-dim': '#0b1612',
        'tertiary-fixed-dim': brass[300],
        primary: moss[300],
        'on-surface': '#e6f0ea',
        'on-surface-variant': '#9fb2a8',
        'surface-variant': '#1c2f28',
        secondary: sage[300],
        'surface-tint': moss[300],
        error: '#ff7b78',
        'secondary-container': '#22362d',
        'primary-container': '#214739',
        'on-tertiary': '#23170d',
        'surface-container-high': '#1d322b',
        'on-background': '#e6f0ea',
        'on-primary-container': '#def0e5',
        'on-error': '#220505',
        'inverse-primary': '#355c49',
        'inverse-surface': '#edf4ef',
        'on-primary-fixed': '#07100d',
        'tertiary-fixed': brass[100],
        'on-primary-fixed-variant': '#3f6b56',
        'inverse-on-surface': ink[950]
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        lg: '1rem',
        xl: '1.5rem',
        full: '9999px'
      },
      fontFamily: {
        headline: ['Inter'],
        body: ['Inter'],
        label: ['Inter']
      }
    }
  },
  plugins: []
}
