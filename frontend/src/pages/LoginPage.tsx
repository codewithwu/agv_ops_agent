/**
 * 登录页面 - 赛博朋克工业风格
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { login } from '../api/auth';
import { useAuthStore } from '../store/authStore';
import '../styles/auth.css';

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !password) {
      message.error('请输入用户名和密码');
      return;
    }

    setLoading(true);
    try {
      const response = await login({ username, password });
      setAuth({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });
      message.success('登录成功');
      navigate('/home');
    } catch (error: any) {
      const detail = error.response?.data?.detail || '登录失败';
      message.error(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-grid" />
      <div className="auth-particles">
        <div className="particle" />
        <div className="particle" />
        <div className="particle" />
        <div className="particle" />
        <div className="particle" />
      </div>

      <div className="auth-card">
        <h1 className="auth-title">登录系统</h1>
        <p className="auth-subtitle">
          还没有账号？<Link to="/register">立即注册</Link>
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-item">
            <label className="form-label">用户名</label>
            <div className="form-input-wrapper">
              <input
                type="text"
                className="form-input"
                placeholder="输入用户名"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <UserOutlined className="form-input-icon" />
            </div>
          </div>

          <div className="form-item">
            <label className="form-label">密码</label>
            <div className="form-input-wrapper">
              <input
                type="password"
                className="form-input"
                placeholder="输入密码"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <LockOutlined className="form-input-icon" />
            </div>
          </div>

          <button
            type="submit"
            className="submit-button"
            disabled={loading}
          >
            {loading ? <span className="loading-spinner" /> : '进入系统'}
          </button>
        </form>
      </div>
    </div>
  );
}
