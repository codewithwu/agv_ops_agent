/**
 * 首页 - 赛博朋克工业风格
 * 根据用户角色显示不同内容：
 * - admin: 标签页切换（用户管理 / 文件管理）
 * - 其他: 仅显示个人信息
 */

import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LogoutOutlined,
  UploadOutlined,
  UserOutlined,
  TeamOutlined,
  FileOutlined,
  EditOutlined,
  DeleteOutlined,
  HolderOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { message, Table, Modal, Select, Switch, Upload, Button, Layout, Menu, Input, Spin } from 'antd';
import type { MenuProps } from 'antd';
import type { UploadProps } from 'antd';

import { logout } from '../api/auth';
import { getCurrentUser } from '../api/auth';
import { listUsers, updateUser } from '../api/user';
import { uploadFile, listFiles, deleteFile, type FileListResponse } from '../api/file';
import { chat } from '../api/agent';
import { useAuthStore } from '../store/authStore';
import type { UserInfo } from '../types/auth';
import '../styles/home.css';

export default function HomePage() {
  const navigate = useNavigate();
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [loading, setLoading] = useState(true);

  // 主题状态
  const [isDarkMode, setIsDarkMode] = useState(true);

  // Admin 功能状态
  const [isAdmin, setIsAdmin] = useState(false);
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [files, setFiles] = useState<FileListResponse['files']>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [filesLoading, setFilesLoading] = useState(false);
  const [editingUser, setEditingUser] = useState<UserInfo | null>(null);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editFormData, setEditFormData] = useState({ role: '', is_active: true });

  // 标签页状态
  const [activeTab, setActiveTab] = useState(isAdmin ? 'users' : 'profile');

  // 侧边栏折叠状态
  const [collapsed, setCollapsed] = useState(false);

  // AI 问答侧边栏状态
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [currentSessionId] = useState(() => `session_${Date.now()}`);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // 获取用户信息
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userInfo = await getCurrentUser();
        setUser(userInfo);
        setIsAdmin(userInfo.role === 'admin');
      } catch (error) {
        console.error('获取用户信息失败:', error);
      } finally {
        setLoading(false);
      }
    };

    if (!user) {
      fetchUser();
    } else {
      setIsAdmin(user.role === 'admin');
      setLoading(false);
    }
  }, [user, setUser]);

  // Admin 加载数据
  useEffect(() => {
    if (isAdmin) {
      fetchUsers();
      fetchFileList();
    }
  }, [isAdmin]);

  const fetchUsers = async () => {
    setUsersLoading(true);
    try {
      const data = await listUsers();
      setUsers(data.users);
    } catch (error) {
      message.error('获取用户列表失败');
    } finally {
      setUsersLoading(false);
    }
  };

  const fetchFileList = async () => {
    setFilesLoading(true);
    try {
      const data = await listFiles();
      setFiles(data.files);
    } catch (error) {
      message.error('获取文件列表失败');
    } finally {
      setFilesLoading(false);
    }
  };

  // 主题切换
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('退出登录失败:', error);
    } finally {
      clearAuth();
      navigate('/login');
    }
  };

  // 文件上传
  const uploadProps: UploadProps = {
    name: 'file',
    showUploadList: false,
    beforeUpload: async (file) => {
      try {
        const result = await uploadFile(file);
        if (result.is_duplicate) {
          message.success('文件已存在，已跳过重复上传');
        } else {
          message.success('文件上传成功');
        }
        fetchFileList();
      } catch (error: any) {
        message.error(error?.response?.data?.detail || '上传失败');
      }
      return false;
    },
  };

  // 删除文件
  const handleDeleteFile = (fileId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该文件吗？此操作不可撤销。',
      okText: '确认',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await deleteFile(fileId);
          message.success('文件删除成功');
          fetchFileList();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  // 编辑用户
  const handleEditUser = (userInfo: UserInfo) => {
    setEditingUser(userInfo);
    setEditFormData({ role: userInfo.role, is_active: userInfo.is_active });
    setEditModalVisible(true);
  };

  const handleSaveUser = async () => {
    if (!editingUser) return;
    try {
      await updateUser(editingUser.id, editFormData);
      message.success('用户信息更新成功');
      setEditModalVisible(false);
      fetchUsers();
    } catch (error) {
      message.error('更新失败');
    }
  };

  // AI 问答
  const handleSendMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      const response = await chat({
        message: userMessage,
        session_id: currentSessionId,
        llm_provider: 'openai',
      });
      setChatMessages((prev) => [...prev, { role: 'assistant', content: response.message }]);
    } catch (error) {
      message.error('发送消息失败，请重试');
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-ring" />
      </div>
    );
  }

  // ===== 非 Admin 视图 - 侧边栏布局 =====
  const nonAdminMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
  ];

  // 非 Admin 内容区
  const profileRecords = [
    {
      id: user?.id,
      username: user?.username || '',
      email: user?.email || '',
      role: user?.role || '',
      is_active: user?.is_active,
    },
  ];

  const handleChangePassword = () => {
    navigate('/change-password');
  };

  const renderNonAdminContent = () => (
    <div className="tab-content">
      <div className="content-header">
        <span className="content-title">个人信息</span>
      </div>
      <Table
        className="data-table"
        dataSource={profileRecords}
        rowKey="id"
        pagination={false}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 60 },
          { title: '用户名', dataIndex: 'username' },
          { title: '邮箱', dataIndex: 'email', ellipsis: true },
          {
            title: '角色',
            dataIndex: 'role',
            render: (role: string) => <span className={`tag-badge ${role}`}>{role}</span>,
          },
          {
            title: '状态',
            dataIndex: 'is_active',
            render: (active: boolean) => (
              <span className={`tag-badge ${active ? 'active' : 'inactive'}`}>
                {active ? '正常' : '禁用'}
              </span>
            ),
          },
          {
            title: '操作',
            width: 100,
            render: () => (
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                className="edit-btn"
                onClick={handleChangePassword}
              >
                修改密码
              </Button>
            ),
          },
        ]}
      />
    </div>
  );

  // ===== Admin 视图 - 侧边栏布局 =====
  const adminMenuItems: MenuProps['items'] = [
    {
      key: 'users',
      icon: <TeamOutlined />,
      label: '用户管理',
    },
    {
      key: 'files',
      icon: <FileOutlined />,
      label: '文件管理',
    },
    {
      key: 'ai-chat',
      icon: <RobotOutlined />,
      label: 'AI 问答',
    },
  ];

  // 根据角色选择菜单
  const menuItems: MenuProps['items'] = isAdmin ? adminMenuItems : nonAdminMenuItems;

  return (
    <div className={`home-container ${isDarkMode ? '' : 'light-mode'}`}>
      <nav className="home-nav">
        <div className="nav-brand">AGV OPS</div>
        <div className="nav-user">
          {isAdmin && <div className="nav-role-badge">管理员</div>}
          <Button
            type="text"
            size="small"
            icon={<HolderOutlined />}
            className="nav-theme-btn"
            onClick={toggleTheme}
            title={isDarkMode ? '切换到白天模式' : '切换到黑夜模式'}
          />
          <div className="nav-username">
            <span>{user?.username}</span>
          </div>
          <Button
            type="text"
            size="small"
            icon={<LogoutOutlined />}
            className="nav-logout-btn"
            onClick={handleLogout}
          />
        </div>
      </nav>

      <main className="home-main admin-main">
        <Layout.Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          trigger={null}
          className="admin-sider"
          width={200}
          collapsedWidth={60}
        >
          <Menu
            mode="inline"
            selectedKeys={[activeTab]}
            onClick={({ key }) => setActiveTab(key)}
            items={menuItems}
            className="admin-menu"
          />
          <div
            className="collapse-trigger"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? '›' : '‹'}
          </div>
        </Layout.Sider>

        <div className="admin-content">
          {/* 非 Admin 用户内容 */}
          {!isAdmin && activeTab === 'profile' && renderNonAdminContent()}

          {/* Admin 用户内容 */}
          {isAdmin && activeTab === 'users' && (
            <div className="tab-content">
              <div className="content-header">
                <span className="content-title">用户列表</span>
                <span className="content-count">{users.length} 位用户</span>
              </div>
              <Table
                className="data-table"
                dataSource={users}
                rowKey="id"
                loading={usersLoading}
                pagination={{ pageSize: 8, size: 'small' }}
                columns={[
                  { title: 'ID', dataIndex: 'id', width: 60 },
                  { title: '用户名', dataIndex: 'username' },
                  { title: '邮箱', dataIndex: 'email', ellipsis: true },
                  {
                    title: '角色',
                    dataIndex: 'role',
                    render: (role: string) => (
                      <span className={`tag-badge ${role}`}>{role}</span>
                    ),
                  },
                  {
                    title: '状态',
                    dataIndex: 'is_active',
                    render: (active: boolean) => (
                      <span className={`tag-badge ${active ? 'active' : 'inactive'}`}>
                        {active ? '正常' : '禁用'}
                      </span>
                    ),
                  },
                  {
                    title: '操作',
                    width: 80,
                    render: (_: unknown, record: UserInfo) => (
                      <Button
                        type="text"
                        size="small"
                        icon={<EditOutlined />}
                        className="edit-btn"
                        onClick={() => handleEditUser(record)}
                      />
                    ),
                  },
                ]}
              />
            </div>
          )}

          {isAdmin && activeTab === 'files' && (
            <div className="tab-content">
              <div className="content-header">
                <span className="content-title">文件列表</span>
                <div className="content-actions">
                  <Upload {...uploadProps}>
                    <Button type="primary" size="small" icon={<UploadOutlined />}>
                      上传文件
                    </Button>
                  </Upload>
                </div>
              </div>
              <Table
                className="data-table"
                dataSource={files}
                rowKey="id"
                loading={filesLoading}
                pagination={{ pageSize: 8, size: 'small' }}
                columns={[
                  { title: '文件名', dataIndex: 'original_filename', ellipsis: true },
                  {
                    title: '大小',
                    dataIndex: 'file_size',
                    width: 100,
                    render: (size: number) => `${(size / 1024).toFixed(1)} KB`,
                  },
                  { title: '类型', dataIndex: 'mime_type', ellipsis: true, width: 150 },
                  {
                    title: '上传时间',
                    dataIndex: 'created_at',
                    width: 180,
                    render: (time: string) => new Date(time).toLocaleString('zh-CN'),
                  },
                  {
                    title: '操作',
                    width: 80,
                    render: (_: unknown, record: { id: number; user_id: number }) => {
                      // 仅当文件属于当前用户时显示删除按钮
                      if (record.user_id !== user?.id) {
                        return null;
                      }
                      return (
                        <Button
                          type="text"
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => handleDeleteFile(record.id)}
                        />
                      );
                    },
                  },
                ]}
              />
            </div>
          )}

          {isAdmin && activeTab === 'ai-chat' && (
            <div className="tab-content ai-chat-container">
              <div className="content-header">
                <span className="content-title">AI 智能问答</span>
              </div>
              <div className="ai-chat-panel">
                <div className="ai-chat-messages" ref={chatContainerRef}>
                  {chatMessages.length === 0 && (
                    <div className="ai-chat-empty">
                      <RobotOutlined style={{ fontSize: 48, color: '#666' }} />
                      <p>您好！我是 AGV 智能助手，可以帮您解答关于 AGV 操作、维护、故障处理等问题。</p>
                      <p>请上传 AGV 相关文档后向我提问。</p>
                    </div>
                  )}
                  {chatMessages.map((item, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        justifyContent: item.role === 'user' ? 'flex-end' : 'flex-start',
                        border: 'none',
                        padding: '8px 0',
                      }}
                    >
                      <div
                        className={`ai-chat-bubble ${item.role === 'user' ? 'user-bubble' : 'assistant-bubble'}`}
                      >
                        {item.content}
                      </div>
                    </div>
                  ))}
                  {chatLoading && (
                    <div className="ai-chat-loading">
                      <Spin size="small" /> AI 正在思考...
                    </div>
                  )}
                </div>
                <div className="ai-chat-input">
                  <Input.Search
                    placeholder="输入您的问题，按回车发送..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onSearch={handleSendMessage}
                    enterButton="发送"
                    loading={chatLoading}
                    disabled={chatLoading}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="home-footer">AGV Operations System</footer>

      {/* 编辑用户 Modal */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onOk={handleSaveUser}
        onCancel={() => setEditModalVisible(false)}
        okText="保存"
        cancelText="取消"
        className="edit-user-modal"
      >
        {editingUser && (
          <div className="edit-user-form">
            <div className="form-info">
              <p>用户名: <strong>{editingUser.username}</strong></p>
              <p>邮箱: {editingUser.email}</p>
            </div>
            <div className="form-field">
              <label>角色</label>
              <Select
                value={editFormData.role}
                onChange={(value) => setEditFormData({ ...editFormData, role: value })}
                style={{ width: '100%' }}
                options={[
                  { value: 'admin', label: '管理员' },
                  { value: 'operator', label: '操作员' },
                  { value: 'viewer', label: '查看者' },
                ]}
              />
            </div>
            <div className="form-field">
              <label>启用状态</label>
              <Switch
                checked={editFormData.is_active}
                onChange={(checked) => setEditFormData({ ...editFormData, is_active: checked })}
                checkedChildren="启用"
                unCheckedChildren="禁用"
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
