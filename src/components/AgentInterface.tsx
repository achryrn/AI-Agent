import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Search, Brain, Microscope, Lightbulb, Cpu, Car, Hand } from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import ToolPanel from './ToolPanel';
import ChatInterface from './ChatInterface';

const AgentInterface = () => {
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Array<{id: string, type: 'user' | 'agent', content: string, timestamp: Date}>>([
    {
      id: '1',
      type: 'agent',
      content: 'Hello! I\'m your AI Agent. I have access to various tools including search capabilities, deep research, analytical thinking, and physical task execution. How can I assist you today?',
      timestamp: new Date()
    }
  ]);

  const tools = [
    {
      id: 'search',
      name: 'Search',
      description: 'Quick web search for immediate information',
      icon: Search,
      color: 'bg-blue-500 hover:bg-blue-600',
      category: 'Information'
    },
    {
      id: 'deep-search',
      name: 'Deep Search',
      description: 'Comprehensive multi-source research with analysis',
      icon: Microscope,
      color: 'bg-purple-500 hover:bg-purple-600',
      category: 'Information'
    },
    {
      id: 'research',
      name: 'Research',
      description: 'Structured research with citations and sources',
      icon: Brain,
      color: 'bg-green-500 hover:bg-green-600',
      category: 'Analysis'
    },
    {
      id: 'deep-thought',
      name: 'Deep Thought',
      description: 'Advanced reasoning and problem-solving analysis',
      icon: Lightbulb,
      color: 'bg-yellow-500 hover:bg-yellow-600',
      category: 'Analysis'
    },
    {
      id: 'physical-task',
      name: 'Physical Tasks',
      description: 'Control physical devices and robotic systems',
      icon: Cpu,
      color: 'bg-red-500 hover:bg-red-600',
      category: 'Physical',
      subTools: [
        {
          id: 'rc-car',
          name: 'RC Car Control',
          description: 'Remote control car navigation and commands',
          icon: Car
        },
        {
          id: 'robotic-arm',
          name: 'Robotic Arm',
          description: 'Precise robotic arm movements and manipulation',
          icon: Hand
        }
      ]
    }
  ];

  const handleToolSelect = (toolId: string) => {
    setSelectedTool(toolId);
    const tool = tools.find(t => t.id === toolId);
    toast({
      title: "Tool Selected",
      description: `${tool?.name} is now active and ready to use.`,
    });
  };

  const handleSendMessage = () => {
    if (!query.trim()) return;
    
    const userMessage = {
      id: Date.now().toString(),
      type: 'user' as const,
      content: query,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsProcessing(true);
    
    // Simulate agent response with tool processing
    setTimeout(() => {
      const agentResponse = {
        id: (Date.now() + 1).toString(),
        type: 'agent' as const,
        content: selectedTool 
          ? `Processing your request with ${tools.find(t => t.id === selectedTool)?.name}... Task completed successfully!`
          : 'I\'ll help you with that. Please select a tool from the panel to get started, or I can suggest the best tool for your request.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, agentResponse]);
      setIsProcessing(false);
    }, 2000);
  };

  const categorizedTools = tools.reduce((acc, tool) => {
    if (!acc[tool.category]) {
      acc[tool.category] = [];
    }
    acc[tool.category].push(tool);
    return acc;
  }, {} as Record<string, typeof tools>);

  return (
    <div className="min-h-screen bg-gray-950 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            AI Agent Interface
          </h1>
          <p className="text-gray-400 text-lg">
            Advanced AI assistant with specialized tools and capabilities
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tools Panel */}
          <div className="lg:col-span-1">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-blue-400" />
                  Available Tools
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(categorizedTools).map(([category, categoryTools]) => (
                  <div key={category}>
                    <h3 className="text-sm font-semibold text-gray-400 mb-2">{category}</h3>
                    <div className="space-y-2">
                      {categoryTools.map((tool) => (
                        <Button
                          key={tool.id}
                          onClick={() => handleToolSelect(tool.id)}
                          variant={selectedTool === tool.id ? "default" : "outline"}
                          className={`w-full justify-start text-left h-auto p-3 ${
                            selectedTool === tool.id 
                              ? 'bg-blue-600 hover:bg-blue-700 text-white border-blue-600' 
                              : 'bg-gray-800 hover:bg-gray-700 text-gray-200 border-gray-700'
                          }`}
                        >
                          <div className="flex items-start gap-3 w-full">
                            <tool.icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="font-medium">{tool.name}</div>
                              <div className="text-xs opacity-75 mt-1">{tool.description}</div>
                            </div>
                          </div>
                        </Button>
                      ))}
                    </div>
                    {category !== 'Physical' && <Separator className="mt-4 bg-gray-800" />}
                  </div>
                ))}
              </CardContent>
            </Card>

            {selectedTool && (
              <div className="mt-4">
                <ToolPanel 
                  selectedTool={selectedTool}
                  tools={tools}
                />
              </div>
            )}
          </div>

          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <ChatInterface 
              messages={messages}
              query={query}
              setQuery={setQuery}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
              selectedTool={selectedTool}
              tools={tools}
            />
          </div>
        </div>

        {/* Status Bar */}
        <div className="mt-6">
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="py-3">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-4">
                  <Badge variant="outline" className="border-green-500 text-green-400 bg-green-500/10">
                    System Online
                  </Badge>
                  {selectedTool && (
                    <Badge variant="outline" className="border-blue-500 text-blue-400 bg-blue-500/10">
                      Active Tool: {tools.find(t => t.id === selectedTool)?.name}
                    </Badge>
                  )}
                </div>
                <div className="text-gray-400">
                  Agent v2.1 | Ready for tasks
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AgentInterface;
