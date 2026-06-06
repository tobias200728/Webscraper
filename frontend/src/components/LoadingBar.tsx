"use client";

export default function LoadingBar({ isVisible }: { isVisible: boolean }) {
  if (!isVisible) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 h-1 bg-gray-200 dark:bg-gray-800">
      <div className="h-full bg-blue-500 animate-[loading_2s_ease-in-out_infinite]" />
      <style jsx>{`
        @keyframes loading {
          0% { width: 0%; margin-left: 0%; }
          50% { width: 70%; margin-left: 15%; }
          100% { width: 0%; margin-left: 100%; }
        }
      `}</style>
    </div>
  );
}
