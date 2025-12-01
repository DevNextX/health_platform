import React, { useEffect, useState } from 'react';
import { Table, Button, Space, Tag, message, Modal, Input, Typography } from 'antd';
import { adminAPI } from '../services/api';
import { getRoleFromToken, getUserIdFromToken } from '../utils/auth';
import { useTranslation } from 'react-i18next';

const { Text } = Typography;

const AdminUsers = () => {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState([]);
  const [resetUserId, setResetUserId] = useState(null);
  const [generatedPwd, setGeneratedPwd] = useState('');
  const { t } = useTranslation();

  const role = getRoleFromToken();
  const meId = getUserIdFromToken();
  const isAdmin = role === 'ADMIN' || role === 'SUPER_ADMIN';
  const isSuper = role === 'SUPER_ADMIN';

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await adminAPI.listUsers();
      setUsers(res.data.items || []);
    } catch (e) {
      message.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAdmin) fetchUsers();
  }, []);

  const columns = [
    { title: t('admin.columns.id') || 'ID', dataIndex: 'id', key: 'id' },
    { title: t('admin.columns.username') || '用户名', dataIndex: 'username', key: 'username' },
    { title: t('admin.columns.email') || '邮箱', dataIndex: 'email', key: 'email' },
    { title: t('admin.columns.role') || '角色', dataIndex: 'role', key: 'role', render: (r) => <Tag color={r === 'SUPER_ADMIN' ? 'red' : r === 'ADMIN' ? 'blue' : 'default'}>{r}</Tag> },
    { title: t('admin.columns.createdAt') || '创建时间', dataIndex: 'created_at', key: 'created_at' },
    { title: t('admin.columns.lastLogin') || '最近登录', dataIndex: 'last_login_at', key: 'last_login_at' },
    {
      title: t('admin.columns.actions') || '操作', key: 'actions',
      render: (_, rec) => (
        <Space>
          {isSuper && rec.role !== 'SUPER_ADMIN' && (
            <>
              {/* 规则：默认仅显示“提升”；只有当角色为 ADMIN 时显示“降级” */}
              {rec.role === 'USER' && (
                <Button size="small" onClick={() => promote(rec.id)}>{t('admin.actions.promote') || '提升'}</Button>
              )}
              {rec.role === 'ADMIN' && (
                <Button size="small" onClick={() => demote(rec.id)}>{t('admin.actions.demote') || '降级'}</Button>
              )}
            </>
          )}
          {isAdmin && (
            <Button size="small" onClick={() => openReset(rec.id)} disabled={meId === rec.id}>
              {t('admin.actions.resetPwd') || '重置密码'}
            </Button>
          )}
        </Space>
      )
    }
  ];

  const promote = async (userId) => {
    try {
      await adminAPI.promoteAdmin(userId);
      message.success(t('admin.messages.promoted') || '已提升');
      fetchUsers();
    } catch (e) {
      message.error(t('admin.messages.promoteFail') || '提升失败');
    }
  };

  const demote = async (userId) => {
    try {
      await adminAPI.demoteAdmin(userId);
      message.success(t('admin.messages.demoted') || '已降级');
      fetchUsers();
    } catch (e) {
      message.error(t('admin.messages.demoteFail') || '降级失败');
    }
  };

  const openReset = (userId) => {
    setResetUserId(userId);
  };

  const doReset = async () => {
    try {
      const res = await adminAPI.resetPassword(resetUserId);
      const pwd = res.data?.temp_password || '';
      setGeneratedPwd(pwd);
      message.success(t('admin.messages.resetOk') || '密码已重置');
      setResetUserId(null);
    } catch (e) {
      const msg = e.response?.data?.message;
      if (msg) {
        message.error(msg);
      } else {
        message.error(t('admin.messages.resetFail') || '重置失败');
      }
    }
  };

  if (!isAdmin) {
    return <Text type="secondary">{t('admin.noAccess') || '无权限'}</Text>;
  }

  return (
    <>
      <Table rowKey="id" loading={loading} dataSource={users} columns={columns} pagination={false} />
      <Modal open={!!resetUserId} title={t('admin.modals.resetTitle') || '重置密码'} onOk={doReset} onCancel={() => setResetUserId(null)} okText={t('common.confirm') || '确认'}>
        <Text type="secondary">{t('admin.modals.autoGen') || '系统将自动生成一个临时密码，并要求用户下次登录时修改密码。'}</Text>
      </Modal>
      <Modal open={!!generatedPwd} title={t('admin.modals.tempPwdTitle') || '临时密码已生成'} onOk={() => setGeneratedPwd('')} onCancel={() => setGeneratedPwd('')} okText={t('common.confirm') || '确认'}>
        <Text strong copyable>{generatedPwd}</Text>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">{t('admin.modals.tempPwdNote') || '请妥善传达给用户，并提醒其尽快修改密码。'}</Text>
        </div>
      </Modal>
    </>
  );
};

export default AdminUsers;
