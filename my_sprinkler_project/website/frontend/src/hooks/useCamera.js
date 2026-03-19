export function useCamera() {
  const streamUrl = import.meta.env.VITE_STREAM_URL || 'http://raspberrypi.local:8080/stream'
  return { streamUrl }
}
