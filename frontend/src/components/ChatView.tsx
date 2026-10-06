'use strict';
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  Bot, 
  User, 
  Send, 
  Loader2, 
  PanelRightClose, 
  PanelRightOpen, 
  Trash2,
  Sparkles
} from 'lucide-react';
import { ChatMessage } from '@/types';
import { ToolCallCollapsible } from './ToolCallCollapsible';

interface ChatViewProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (text: string) => void;
  onClearChat: () => void;
  showScenarios: boolean;
  onToggleScenarios: () => void;
}

export function ChatView({
  messages,
  isLoading,
  onSendMessage,
  onClearChat,
  showScenarios,
  onToggleScenarios,
}: ChatViewProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const text = inputValue.trim();
    if (!text || isLoading) return;
    onSendMessage(text);
    setInputValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const renderFormattedText = (text: string) => {
    // Process markdown bolding and line breaks
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Bold text processing: **word**
      const parts = line.split(/(\*\*.*?\*\*)/g);
      return (
        <span key={idx} className="block min-h-[1.25rem]">
          {parts.map((part, pIdx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return (
                <strong key={pIdx} className="font-semibold text-slate-900">
                  {part.slice(2, -2)}
                </strong>
              );
            }
            return <React.Fragment key={pIdx}>{part}</React.Fragment>;
          })}
        </span>
      );
    });
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] overflow-hidden">
      {/* Chat Top Header */}
      <header className="px-5 py-3 border-b border-slate-200 bg-white flex items-center justify-between shrink-0 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
              <Bot className="w-4 h-4" />
            </div>
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white"></span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-slate-900 leading-tight">Mèo Con</h2>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                Sales Copilot
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">
              Trực tuyến · Dữ liệu kho thật 100% qua MCP Protocol
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={onClearChat}
            title="Xóa lịch sử chat"
            className="p-1.5 rounded-md text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={onToggleScenarios}
            title={showScenarios ? 'Thu gọn kịch bản' : 'Mở rộng kịch bản'}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition-colors"
          >
            {showScenarios ? (
              <>
                <PanelRightClose className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Ẩn kịch bản</span>
              </>
            ) : (
              <>
                <PanelRightOpen className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Kịch bản test</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4 space-y-4">
        {messages.map((msg) => {
          const isAgent = msg.sender === 'agent';
          return (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-3xl ${isAgent ? 'mr-auto' : 'ml-auto flex-row-reverse'}`}
            >
              {/* Avatar */}
              <div className="shrink-0 mt-0.5">
                {isAgent ? (
                  <div className="w-7 h-7 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-2xs">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                ) : (
                  <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 shadow-2xs">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>

              {/* Message Bubble Container */}
              <div className={`space-y-1 max-w-[85%] ${isAgent ? 'text-left' : 'text-right'}`}>
                {/* Meta info */}
                <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono px-1">
                  <span>{isAgent ? 'Mèo Con' : 'Bạn'}</span>
                  <span>·</span>
                  <span>{msg.timestamp}</span>
                </div>

                {/* Agent Tool Calls Accordion */}
                {isAgent && msg.tool_calls && msg.tool_calls.length > 0 && (
                  <div className="space-y-1 mb-2">
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono font-medium px-1">
                      <Sparkles className="w-3 h-3 text-blue-500" />
                      <span>Các lệnh gọi Tool nghiệp vụ ({msg.tool_calls.length})</span>
                    </div>
                    {msg.tool_calls.map((tool, tIdx) => (
                      <ToolCallCollapsible key={tIdx} toolCall={tool} />
                    ))}
                  </div>
                )}

                {/* Text Content Bubble */}
                <div
                  className={`p-3.5 rounded-xl text-xs sm:text-sm leading-relaxed whitespace-pre-wrap break-words ${
                    isAgent
                      ? 'bg-white border border-slate-200 text-slate-800 shadow-2xs rounded-tl-xs'
                      : 'bg-blue-600 text-white shadow-2xs rounded-tr-xs selection:bg-blue-800'
                  }`}
                >
                  {renderFormattedText(msg.text)}
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex gap-3 max-w-3xl mr-auto">
            <div className="w-7 h-7 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shrink-0">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="p-3 rounded-xl bg-white border border-slate-200 text-xs text-slate-600 shadow-2xs flex items-center gap-2 font-medium">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600" />
              <span>Mèo Con đang tra cứu dữ liệu kho qua MCP...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Composer (Intercom style) */}
      <div className="p-4 bg-white border-t border-slate-200 shrink-0">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="border border-slate-200 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 rounded-xl bg-white shadow-2xs transition-all overflow-hidden">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputValue}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Nhập yêu cầu tư vấn (ví dụ: cần laptop code Docker 28tr, bớt giá 2tr, còn hàng không...)"
              className="w-full px-3.5 py-2.5 text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 bg-transparent resize-none outline-none max-h-32 leading-relaxed"
            />

            <div className="px-3 py-1.5 bg-slate-50/50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
              <span className="hidden sm:inline">
                Nhấn <kbd className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200 text-slate-500">Enter</kbd> để gửi · <kbd className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200 text-slate-500">Shift + Enter</kbd> xuống dòng
              </span>
              <span className="sm:hidden font-mono text-[10px]">Nhấn Gửi</span>

              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
              >
                <span>Gửi</span>
                <Send className="w-3 h-3" />
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
