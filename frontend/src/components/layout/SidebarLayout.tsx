"use client";

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Upload, FileText } from 'lucide-react';
import { Button } from "@/components/ui/Button";
import { cn } from '@/lib/utils';
import { DocumentManager } from '@/components/features/upload/DocumentManager';

export interface SidebarLayoutProps {
  children: React.ReactNode;
  apiKey: string;
  onDocumentModeEntered?: () => void;
  onError?: (error: string) => void;
}

const SidebarLayout: React.FC<SidebarLayoutProps> = ({
  children,
  apiKey,
  onDocumentModeEntered,
  onError
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(400);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div
        className={cn(
          "flex-shrink-0 border-r transition-all duration-300 ease-in-out",
          sidebarOpen ? "w-96" : "w-0"
        )}
        style={{ 
          width: sidebarOpen ? `${sidebarWidth}px` : '0px',
          backgroundColor: '#f5f4ed'
        }}
      >
        {sidebarOpen && (
          <div className="h-full flex flex-col">
            {/* Sidebar Header */}
            <div className="flex-shrink-0 p-4 border-b" style={{ backgroundColor: '#f5f4ed' }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Upload className="w-5 h-5 text-primary" />
                  <h2 className="font-semibold text-foreground">Documents & Media</h2>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleSidebar}
                  className="h-8 w-8 p-0"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Sidebar Content */}
            <div className="flex-1 overflow-hidden p-4">
              <DocumentManager
                apiKey={apiKey}
                onDocumentModeEntered={onDocumentModeEntered}
                onError={onError}
                className="h-full"
              />
            </div>
          </div>
        )}
      </div>

      {/* Sidebar Toggle Button (when closed) */}
      {!sidebarOpen && (
        <div className="flex-shrink-0 w-12 border-r flex items-start justify-center pt-4" style={{ backgroundColor: '#f5f4ed' }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            className="h-8 w-8 p-0"
            title="Open Documents Panel"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {children}
      </div>
    </div>
  );
};

export default SidebarLayout;
