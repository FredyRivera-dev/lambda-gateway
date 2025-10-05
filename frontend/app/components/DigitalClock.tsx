"use client"

import { useState, useEffect } from "react"

type DatePosition = "above" | "below" | "hidden"

// Kanji representation of months
const monthKanji = ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]

// Kanji representation of numbers 1-31 for days
const dayKanji = [
  "一",
  "二",
  "三",
  "四",
  "五",
  "六",
  "七",
  "八",
  "九",
  "十",
  "十一",
  "十二",
  "十三",
  "十四",
  "十五",
  "十六",
  "十七",
  "十八",
  "十九",
  "二十",
  "二十一",
  "二十二",
  "二十三",
  "二十四",
  "二十五",
  "二十六",
  "二十七",
  "二十八",
  "二十九",
  "三十",
  "三十一",
]

export default function DigitalClock() {
  const [time, setTime] = useState<Date | null>(null)

  useEffect(() => {
    // Establece la hora inmediatamente al montar
    setTime(new Date())

    const timer = setInterval(() => {
      setTime(new Date())
    }, 1000)

    return () => {
      clearInterval(timer)
    }
  }, [])

  const formatTime = (date: Date) => {
    const hours = date.getHours().toString().padStart(2, "0")
    const minutes = date.getMinutes().toString().padStart(2, "0")
    const seconds = date.getSeconds().toString().padStart(2, "0")
    return `${hours}:${minutes}:${seconds}`
  }

  const formatJapaneseDate = (date: Date) => {
    const day = date.getDate() - 1 // Array is 0-indexed
    const month = date.getMonth() // Array is 0-indexed
    const year = date.getFullYear()

    return `${dayKanji[day]}日 ${monthKanji[month]} ${year}年`
  }

  if (!time) {
    return (
      <div className="relative text-7xl font-bold text-primary bg-transparent p-4 font-mono">
        <div className="flex flex-col items-center">
          <div>--:--:--</div>
          <div className="text-xl mt-2 text-primary/60">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative text-7xl font-bold text-primary bg-transparent p-4 font-mono">
      <div className="flex flex-col items-center">
        <div>{formatTime(time)}</div>
        <div className="text-xl mt-2 text-primary/60">{formatJapaneseDate(time)}</div>
      </div>
    </div>
  )
}
