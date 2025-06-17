import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Settings } from 'lucide-react';

interface ToolPanelProps {
  selectedTool: string;
  tools: any[];
}

const ToolPanel = ({ selectedTool, tools }: ToolPanelProps) => {
  const currentTool = tools.find(t => t.id === selectedTool);

  if (!currentTool) return null;

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <currentTool.icon className="w-5 h-5 text-blue-400" />
          {currentTool.name}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Tool Info */}
        <div className="pt-2">
          <div className="flex items-center gap-2 mb-2">
            <Settings className="w-4 h-4 text-gray-400" />
            <span className="text-sm font-medium text-gray-400">Tool Information</span>
          </div>
          <p className="text-sm text-gray-300 mb-4">
            {currentTool.description}
          </p>
          
          {/* Show sub-tools for physical tasks */}
          {selectedTool === 'physical-task' && currentTool.subTools && (
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Available Devices:</h4>
              <div className="space-y-2">
                {currentTool.subTools.map((subTool: any) => (
                  <Badge 
                    key={subTool.id} 
                    variant="outline" 
                    className="border-green-500 text-green-400 bg-green-500/10 mr-2"
                  >
                    <subTool.icon className="w-3 h-3 mr-1" />
                    {subTool.name}
                  </Badge>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Use the chat to control these devices with natural language commands.
              </p>
            </div>
          )}
          
          <div className="mt-4 p-3 bg-gray-800 rounded-lg">
            <p className="text-xs text-gray-400">
              💬 Use the chat interface to interact with this tool. Simply type your request or command.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ToolPanel;
