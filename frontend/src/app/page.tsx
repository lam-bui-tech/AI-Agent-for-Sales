'use strict';
'use client';

import React, { useState, useEffect } from 'react';
import { Sidebar, NavTab } from '@/components/Sidebar';
import { ChatView } from '@/components/ChatView';
import { QuickScenarios } from '@/components/QuickScenarios';
import { CatalogView } from '@/components/CatalogView';
import { CrmView } from '@/components/CrmView';
import { AuditLogsView } from '@/components/AuditLogsView';
import { ZaloModal } from '@/components/ZaloModal';
import { ChatMessage } from '@/types';
import { sendChatMessage } from '@/lib/api';

const INITIAL_MESSAGE: ChatMessage = {
  id: 'init-msg-1',
  sender: 'agent',
  text: 'Chào bạn! Mình là Mèo Con, trợ lý tư vấn thiết bị công nghệ cho DemoTech.\n\nMình tư vấn nhanh gọn, không đoán mò, có gì cần thì tra dữ liệu thật từ kho.\n\n**Bạn đang cần tìm laptop phân khúc nào hay ngân sách khoảng bao nhiêu ạ?**',
  timestamp: 'Hệ thống DemoTech',
  tool_calls: [],
};

export default function Home() {
  const [currentTab, setCurrentTab] = useState<NavTab>('chat');
  const [messages, setMessages] = useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [isLoading, setIsLoading] = useState(false);
  const [showScenarios, setShowScenarios] = useState(true);
  const [isZaloModalOpen, setIsZaloModalOpen] = useState(false);
  const [userId, setUserId] = useState<string>('web_user_1');

  useEffect(() => {
    // Generate or retrieve persistent user session ID
    let storedId = sessionStorage.getItem('demotech_user_id');
    if (!storedId) {
      storedId = 'web_user_' + Math.random().toString(36).substring(2, 9);
      sessionStorage.setItem('demotech_user_id', storedId);
    }
    setUserId(storedId);
  }, []);

  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await sendChatMessage(text, userId);
      const agentMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: 'agent',
        text: res.reply || 'Dạ hệ thống chưa có phản hồi.',
        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        source: res.source,
        tool_calls: res.tool_calls || [],
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      const errorMsg: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: 'agent',
        text: 'Lỗi kết nối tới hệ thống máy chủ FastAPI. Vui lòng kiểm tra lại dịch vụ hoặc thử lại!',
        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetChat = () => {
    const newId = 'web_user_' + Math.random().toString(36).substring(2, 9);
    sessionStorage.setItem('demotech_user_id', newId);
    setUserId(newId);
    setMessages([
      {
        id: `reset-${Date.now()}`,
        sender: 'agent',
        text: 'Phiên hội thoại mới đã được thiết lập. Bạn cần tư vấn dòng laptop nào hay mức ngân sách bao nhiêu ạ?',
        timestamp: 'Hệ thống DemoTech',
        tool_calls: [],
      },
    ]);
  };

  const handleSelectScenario = (promptText: string) => {
    setCurrentTab('chat');
    handleSendMessage(promptText);
  };

  const handleAskAboutProduct = (promptText: string) => {
    setCurrentTab('chat');
    handleSendMessage(promptText);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#f8fafc] text-slate-900 font-sans">
      {/* 1. Left Sidebar (Linear Style) */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        onOpenZalo={() => setIsZaloModalOpen(true)}
        onResetChat={handleResetChat}
      />

      {/* 2. Main Workspace */}
      <main className="flex-1 flex overflow-hidden">
        {currentTab === 'chat' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Center Chat View */}
            <ChatView
              messages={messages}
              isLoading={isLoading}
              onSendMessage={handleSendMessage}
              onClearChat={handleResetChat}
              showScenarios={showScenarios}
              onToggleScenarios={() => setShowScenarios(!showScenarios)}
            />

            {/* Right Quick Scenarios Column */}
            {showScenarios && (
              <div className="w-80 shrink-0 hidden lg:block h-full animate-in slide-in-from-right-4 duration-200">
                <QuickScenarios
                  onSelectScenario={handleSelectScenario}
                  isLoading={isLoading}
                />
              </div>
            )}
          </div>
        )}

        {currentTab === 'catalog' && (
          <CatalogView onAskAboutProduct={handleAskAboutProduct} />
        )}

        {currentTab === 'crm' && <CrmView />}

        {currentTab === 'audit' && <AuditLogsView />}
      </main>

      {/* 3. Zalo Login Modal */}
      <ZaloModal
        isOpen={isZaloModalOpen}
        onClose={() => setIsZaloModalOpen(false)}
      />
    </div>
  );
}
