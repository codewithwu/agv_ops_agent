/**
 * 注册页面 - 赛博朋克工业风格
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { message } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { register } from '../api/auth';
import '../styles/auth.css';

export default function RegisterPage() {
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !email || !password || !confirmPassword) {
      message.error('请填写所有字段');
      return;
    }

    if (password !== confirmPassword) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      await register({ username, email, password });
      message.success('注册成功，请登录');
      navigate('/login');
    } catch (error: any) {
      const detail = error.response?.data?.detail || '注册失败';
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
        <h1 className="auth-title">创建账号</h1>
        <p className="auth-subtitle">
          已有账号？<Link to="/login">立即登录</Link>
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-item">
            <label className="form-label">用户名</label>
            <div className="form-input-wrapper">
              <input
                type="text"
                className="form-input"
                placeholder="3-20个字符"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <UserOutlined className="form-input-icon" />
            </div>
          </div>

          <div className="form-item">
            <label className="form-label">邮箱</label>
            <div className="form-input-wrapper">
              <input
                type="email"
                className="form-input"
                placeholder="输入邮箱地址"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <MailOutlined className="form-input-icon" />
            </div>
          </div>

          <div className="form-item">
            <label className="form-label">密码</label>
            <div className="form-input-wrapper">
              <input
                type="password"
                className="form-input"
                placeholder="6-50个字符"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <LockOutlined className="form-input-icon" />
            </div>
          </div>

          <div className="form-item">
            <label className="form-label">确认密码</label>
            <div className="form-input-wrapper">
              <input
                type="password"
                className="form-input"
                placeholder="再次输入密码"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
              <LockOutlined className="form-input-icon" />
            </div>
          </div>

          <button
            type="submit"
            className="submit-button"
            disabled={loading}
          >
            {loading ? <span className="loading-spinner" /> : '注册账号'}
          </button>
        </form>
      </div>
    </div>
  );
}
