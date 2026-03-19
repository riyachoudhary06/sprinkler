import { useEffect } from 'react'
import mqtt from 'mqtt'
export function useMQTT(broker, topics, onMessage) {
  useEffect(() => {
    const client = mqtt.connect(broker)
    client.on('connect', () => topics.forEach(t => client.subscribe(t)))
    client.on('message', (topic, payload) => onMessage(topic, payload.toString()))
    return () => client.end()
  }, [broker])
}
