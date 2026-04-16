/**
 * 首页 - 赛博朋克工业风格
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogoutOutlined, KeyOutlined } from '@ant-design/icons';
import { logout } from '../api/auth';
import { getCurrentUser } from '../api/auth';
import { useAuthStore } from '../store/authStore';
import '../styles/home.css';

export default function HomePage() {
  const navigate = useNavigate();
  const clearAuth = useAuthStore((state) => state.clearAuth);
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userInfo = await getCurrentUser();
        setUser(userInfo);
      } catch (error) {
        console.error('获取用户信息失败:', error);
      } finally {
        setLoading(false);
      }
    };

    if (!user) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [user, setUser]);

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

  const handleChangePassword = () => {
    navigate('/change-password');
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-ring" />
      </div>
    );
  }

  return (
    <div className="home-container">
      {/* 导航栏 */}
      <nav className="home-nav">
        <div className="nav-brand">AGV OPS</div>
        <div className="nav-user">
          <div className="nav-username">
            当前用户: <span>{user?.username || '未知'}</span>
          </div>
        </div>
      </nav>

      {/* 主内容 */}
      <main className="home-main">
        <div className="home-card">
          <h1 className="home-title">hello world</h1>
          <p className="home-subtitle">
            欢迎回来，<span>{user?.username}</span>
          </p>

          <div className="home-actions">
            <button className="home-button" onClick={handleChangePassword}>
              <KeyOutlined />
              修改密码
            </button>
            <button className="home-button danger" onClick={handleLogout}>
              <LogoutOutlined />
              退出登录
            </button>
          </div>
        </div>
      </main>

      {/* 底部装饰 */}
      <footer className="home-footer">
        AGV Operations System
      </footer>
    </div>
  );
}
