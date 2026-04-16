/**
 * 修改密码页面 - 赛博朋克工业风格
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { changePassword } from '../api/auth';
import { useAuthStore } from '../store/authStore';
import '../styles/auth.css';

export default function ChangePasswordPage() {
  const [loading, setLoading] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const navigate = useNavigate();
  const clearAuth = useAuthStore((state) => state.clearAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!oldPassword || !newPassword || !confirmPassword) {
      message.error('请填写所有字段');
      return;
    }

    if (newPassword !== confirmPassword) {
      message.error('两次输入的新密码不一致');
      return;
    }

    if (oldPassword === newPassword) {
      message.error('新密码不能与旧密码相同');
      return;
    }

    setLoading(true);
    try {
      await changePassword({
        old_password: oldPassword,
        new_password: newPassword,
      });
      message.success('密码修改成功，请重新登录');
      clearAuth();
      navigate('/login');
    } catch (error: any) {
      const detail = error.response?.data?.detail || '修改密码失败';
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
        <h1 className="auth-title">修改密码</h1>
        <p className="auth-subtitle">请输入旧密码和新密码</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-item">
            <label className="form-label">旧密码</label>
            <div className="form-input-wrapper">
              <input
                type="password"
                className="form-input"
                placeholder="输入旧密码"
                autoComplete="current-password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
              />
              <LockOutlined className="form-input-icon" />
            </div>
          </div>

          <div className="form-item">
            <label className="form-label">新密码</label>
            <div className="form-input-wrapper">
              <input
                type="password"
                className="form-input"
                placeholder="6-50个字符"
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <LockOutlined className="form-input-icon" />
            </div>
          </div>

          <div className="form-item">
            <label className="form-label">确认新密码</label>
            <div className="form-input-wrapper">
              <input
                type="password"
                className="form-input"
                placeholder="再次输入新密码"
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
            {loading ? <span className="loading-spinner" /> : '确认修改'}
          </button>
        </form>
      </div>
    </div>
  );
}
