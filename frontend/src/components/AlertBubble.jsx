export function AlertBubble({ message }) {
  if (!message) return null
  return (
    <div className="mt-2 w-fit max-w-[50%] rounded-xl border border-red-100 bg-red-50 px-3 py-2 shadow-subtle">
      <div className="text-xs leading-5 text-red-400">{message}</div>
    </div>
  )
}

