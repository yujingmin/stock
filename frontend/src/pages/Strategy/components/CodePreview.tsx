/**
 * 代码预览组件
 */
import React from 'react';
import { Card, Button, Space } from 'antd';
import { CopyOutlined, DownloadOutlined } from '@ant-design/icons';
import './CodePreview.css';

interface CodePreviewProps {
  code: string;
  language?: string;
  title?: string;
}

const CodePreview: React.FC<CodePreviewProps> = ({ code, language = 'python', title = '代码预览' }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(code);
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `strategy.${language === 'python' ? 'py' : 'txt'}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card
      title={title}
      className="code-preview"
      extra={
        <Space>
          <Button icon={<CopyOutlined />} onClick={handleCopy} size="small">
            复制
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleDownload} size="small">
            下载
          </Button>
        </Space>
      }
    >
      <pre className="code-block" style={{ margin: 0, overflow: 'auto', maxHeight: '500px' }}>
        <code className={`language-${language}`}>{code}</code>
      </pre>
    </Card>
  );
};

export default CodePreview;
