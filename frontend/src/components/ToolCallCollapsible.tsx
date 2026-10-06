'use strict';
'use client';

import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronRight, 
  Search, 
  Package, 
  UserCheck, 
  ShieldAlert, 
  FileText, 
  Terminal, 
  CheckCircle2, 
  XCircle,
  Copy,
  Check
} from 'lucide-react';
import { ToolCall } from '@/types';

interface ToolCallCollapsibleProps {
  toolCall: ToolCall;
}

export function ToolCallCollapsible({ toolCall }: ToolCallCollapsibleProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copiedInput, setCopiedInput] = useState(false);
  const [copiedOutput, setCopiedOutput] = useState(false);

  const getToolIcon = (name: string) => {
    switch (name) {
      case 'search_products':
        return <Search className="w-3.5 h-3.5 text-blue-600" />;
      case 'check_inventory':
        return <Package className="w-3.5 h-3.5 text-emerald-600" />;
      case 'create_lead':
        return <UserCheck className="w-3.5 h-3.5 text-purple-600" />;
      case 'handoff_to_human':
        return <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />;
      case 'get_policy_answer':
        return <FileText className="w-3.5 h-3.5 text-sky-600" />;
      default:
        return <Terminal className="w-3.5 h-3.5 text-slate-600" />;
    }
  };

  const formatJson = (val: any) => {
    if (!val) return '{}';
    if (typeof val === 'string') {
      try {
        return JSON.stringify(JSON.parse(val), null, 2);
      } catch {
        return val;
      }
    }
    return JSON.stringify(val, null, 2);
  };

  const copyToClipboard = (text: string, type: 'input' | 'output') => {
    navigator.clipboard.writeText(text);
    if (type === 'input') {
      setCopiedInput(true);
      setTimeout(() => setCopiedInput(false), 1500);
    } else {
      setCopiedOutput(true);
      setTimeout(() => setCopiedOutput(false), 1500);
    }
  };

  const duration = toolCall.execution_time_ms ?? toolCall.duration_ms ?? 0;
  const isSuccess = toolCall.success === true || toolCall.success === 1 || toolCall.success === undefined;
  const inputStr = formatJson(toolCall.input_payload);
  const outputStr = formatJson(toolCall.output_payload);

  return (
    <div className="my-1.5 border border-slate-200 rounded-md bg-white shadow-xs overflow-hidden transition-all text-xs">
      {/* Header bar (Collapsible trigger) */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-2.5 py-1.5 hover:bg-slate-50 transition-colors text-left"
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="p-1 rounded bg-slate-100 flex items-center justify-center shrink-0">
            {getToolIcon(toolCall.tool_name)}
          </div>
          <span className="font-mono font-medium text-slate-800 truncate">
            {toolCall.tool_name}
          </span>
          <span className="text-slate-400 font-mono text-[11px]">
            {duration > 0 ? `${duration.toFixed(1)}ms` : '<1ms'}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${
            isSuccess 
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
              : 'bg-rose-50 text-rose-700 border border-rose-200'
          }`}>
            {isSuccess ? (
              <>
                <CheckCircle2 className="w-2.5 h-2.5 text-emerald-600" />
                <span>Success</span>
              </>
            ) : (
              <>
                <XCircle className="w-2.5 h-2.5 text-rose-600" />
                <span>Failed</span>
              </>
            )}
          </span>

          <div className="text-slate-400 p-0.5">
            {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          </div>
        </div>
      </button>

      {/* Expanded Accordion Body */}
      {isOpen && (
        <div className="border-t border-slate-100 bg-slate-50/70 p-2.5 space-y-2 font-mono">
          {/* Input Block */}
          <div>
            <div className="flex items-center justify-between text-[11px] text-slate-500 font-sans font-medium mb-1">
              <span>Tham số đầu vào (Input Payload)</span>
              <button
                type="button"
                onClick={() => copyToClipboard(inputStr, 'input')}
                className="flex items-center gap-1 text-slate-500 hover:text-slate-900 transition-colors px-1 py-0.5 rounded hover:bg-slate-200"
              >
                {copiedInput ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                <span>{copiedInput ? 'Đã chép' : 'Sao chép'}</span>
              </button>
            </div>
            <pre className="p-2 rounded bg-white border border-slate-200 text-slate-800 text-[11px] overflow-x-auto max-h-40 leading-relaxed">
              {inputStr}
            </pre>
          </div>

          {/* Output Block */}
          {toolCall.output_payload && (
            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-500 font-sans font-medium mb-1">
                <span>Kết quả phản hồi từ API (Output Result)</span>
                <button
                  type="button"
                  onClick={() => copyToClipboard(outputStr, 'output')}
                  className="flex items-center gap-1 text-slate-500 hover:text-slate-900 transition-colors px-1 py-0.5 rounded hover:bg-slate-200"
                >
                  {copiedOutput ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedOutput ? 'Đã chép' : 'Sao chép'}</span>
                </button>
              </div>
              <pre className="p-2 rounded bg-white border border-slate-200 text-slate-800 text-[11px] overflow-x-auto max-h-48 leading-relaxed">
                {outputStr}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
