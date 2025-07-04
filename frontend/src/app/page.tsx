"use client";
import { ChatForm } from "@/components/ChatForm";
import { MessageStream } from "@/components/MessageStream";
import { LoadingIndicator } from "@/components/LoadingIndicator";
import { ErrorDisplay } from "@/components/ErrorDisplay";
import { useChat } from "@/hooks/useChat";

export default function Home() {
  const { message, loading, error, sendChat } = useChat();

  return (
    <div className="flex flex-col items-center min-h-screen bg-gradient-to-br from-blue-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-950 dark:to-gray-900 p-4 sm:p-8">
      <h1 className="text-3xl font-bold mb-6 mt-8 text-blue-700 dark:text-blue-300">OpenAI Chat Playground</h1>
      <ChatForm
        onSubmit={sendChat}
        loading={loading}
      />
      <div className="my-6 w-full flex flex-col items-center">
        {loading && <LoadingIndicator />}
        {error && <ErrorDisplay error={error} />}
        <MessageStream message={message} loading={loading} />
      </div>
      <footer className="mt-auto text-xs text-gray-500 dark:text-gray-400 py-4">
        Powered by Next.js, Tailwind CSS, and OpenAI
      </footer>
    </div>
  );
}
