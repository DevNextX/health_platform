/**
 * Super Admin Settings Page: Threshold Configuration Governance
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Button,
  Typography,
  message,
  Space,
  Row,
  Col,
  Divider,
  Alert,
  Modal,
  Table,
  Statistic,
  Spin,
  Tag,
} from 'antd';
import {
  SaveOutlined,
  CloudUploadOutlined,
  ReloadOutlined,
  DownloadOutlined,
  HistoryOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { superAdminAPI } from '../services/api';
import { getRoleFromToken } from '../utils/auth';

const { Title, Text } = Typography;

const SuperAdminSettings = () => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [activeConfig, setActiveConfig] = useState(null);
  const [draftConfig, setDraftConfig] = useState(null);
  const [safetyBounds, setSafetyBounds] = useState({});
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showAuditLogs, setShowAuditLogs] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const role = getRoleFromToken();
  const isSuperAdmin = role === 'SUPER_ADMIN';

  // Fetch current configuration
  const fetchConfig = useCallback(async () => {
    try {
      setLoading(true);
      const [activeRes, draftRes] = await Promise.all([
        superAdminAPI.getActiveThresholds(),
        isSuperAdmin ? superAdminAPI.getDraftThreshold() : Promise.resolve({ data: { draft: null } }),
      ]);

      const active = activeRes.data;
      setActiveConfig(active);
      setSafetyBounds(active.safety_bounds || {});

      const draft = draftRes.data.draft;
      setDraftConfig(draft);

      // Set form values from draft if exists, otherwise from active
      const config = draft?.config || active.config;
      form.setFieldsValue(config);
    } catch (error) {
      console.error('Failed to fetch config:', error);
      message.error(t('superAdmin.messages.loadFail') || 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  }, [form, isSuperAdmin, t]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  // Save as draft
  const handleSaveDraft = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const res = await superAdminAPI.createDraft(values);
      setDraftConfig({ id: res.data.id, config: res.data.config, version: res.data.version });
      message.success(t('superAdmin.messages.draftSaved') || 'Draft saved successfully');
    } catch (error) {
      console.error('Failed to save draft:', error);
      const details = error.response?.data?.details;
      if (details) {
        message.error(details.join(', '));
      } else {
        message.error(t('superAdmin.messages.saveFail') || 'Failed to save draft');
      }
    } finally {
      setSaving(false);
    }
  };

  // Preview impact
  const handlePreview = async () => {
    try {
      const values = await form.validateFields();
      const res = await superAdminAPI.previewImpact(values);
      setPreviewData(res.data);
      setShowPreview(true);
    } catch (error) {
      console.error('Failed to preview:', error);
      message.error(t('superAdmin.messages.previewFail') || 'Failed to generate preview');
    }
  };

  // Publish draft
  const handlePublish = async () => {
    if (!draftConfig) {
      message.warning(t('superAdmin.messages.noDraft') || 'Please save a draft first');
      return;
    }

    Modal.confirm({
      title: t('superAdmin.modals.publishTitle') || 'Publish Configuration',
      content: t('superAdmin.modals.publishContent') || 'This will make the draft configuration active for all users. Continue?',
      okText: t('common.confirm') || 'Confirm',
      cancelText: t('common.cancel') || 'Cancel',
      onOk: async () => {
        try {
          setPublishing(true);
          await superAdminAPI.publishDraft(draftConfig.id);
          message.success(t('superAdmin.messages.published') || 'Configuration published successfully');
          fetchConfig();
        } catch (error) {
          console.error('Failed to publish:', error);
          message.error(t('superAdmin.messages.publishFail') || 'Failed to publish configuration');
        } finally {
          setPublishing(false);
        }
      },
    });
  };

  // Reset to default
  const handleReset = async () => {
    Modal.confirm({
      title: t('superAdmin.modals.resetTitle') || 'Reset to Default',
      content: t('superAdmin.modals.resetContent') || 'This will create a draft with default values. Continue?',
      okText: t('common.confirm') || 'Confirm',
      cancelText: t('common.cancel') || 'Cancel',
      onOk: async () => {
        try {
          const res = await superAdminAPI.resetToDefault();
          setDraftConfig({ id: res.data.id, config: res.data.config, version: res.data.version });
          form.setFieldsValue(res.data.config);
          message.success(t('superAdmin.messages.resetDone') || 'Draft created with default values');
        } catch (error) {
          console.error('Failed to reset:', error);
          message.error(t('superAdmin.messages.resetFail') || 'Failed to reset to defaults');
        }
      },
    });
  };

  // Fetch audit logs
  const handleShowAuditLogs = async () => {
    try {
      setAuditLoading(true);
      const res = await superAdminAPI.getAuditLogs({ page: 1, size: 50 });
      setAuditLogs(res.data.logs || []);
      setShowAuditLogs(true);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
      message.error(t('superAdmin.messages.auditFail') || 'Failed to load audit logs');
    } finally {
      setAuditLoading(false);
    }
  };

  // Export audit logs as CSV
  const handleExportAuditLogs = async () => {
    try {
      const res = await superAdminAPI.exportAuditLogs();
      const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'threshold_audit_logs.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export:', error);
      message.error(t('superAdmin.messages.exportFail') || 'Failed to export audit logs');
    }
  };

  // Audit log table columns
  const auditColumns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: t('superAdmin.audit.action') || 'Action', dataIndex: 'action', key: 'action', width: 100, render: (a) => <Tag color={a === 'published' ? 'green' : 'blue'}>{a}</Tag> },
    { title: t('superAdmin.audit.operator') || 'Operator', dataIndex: ['operator', 'username'], key: 'operator', width: 120 },
    { title: t('superAdmin.audit.time') || 'Time', dataIndex: 'created_at', key: 'created_at', width: 180 },
    { title: t('superAdmin.audit.newConfig') || 'New Config', dataIndex: 'new_config', key: 'new_config', render: (c) => <Text code style={{ fontSize: 11 }}>{JSON.stringify(c)}</Text> },
  ];

  if (!isSuperAdmin) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          type="error"
          message={t('superAdmin.noAccess') || 'Access Denied'}
          description={t('superAdmin.noAccessDesc') || 'Only Super Administrators can access this page.'}
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>{t('superAdmin.title') || 'Super Admin Settings'}</Title>
        <Space>
          <Button icon={<HistoryOutlined />} onClick={handleShowAuditLogs} loading={auditLoading}>
            {t('superAdmin.auditLogs') || 'Audit Logs'}
          </Button>
        </Space>
      </div>

      {/* Current Active Config Info */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title={t('superAdmin.activeVersion') || 'Active Version'}
              value={activeConfig?.version || 0}
              prefix="v"
            />
          </Col>
          <Col span={8}>
            <Statistic
              title={t('superAdmin.publishedAt') || 'Published At'}
              value={activeConfig?.published_at || '-'}
              valueStyle={{ fontSize: 14 }}
            />
          </Col>
          <Col span={8}>
            {draftConfig && (
              <Statistic
                title={t('superAdmin.draftVersion') || 'Draft Version'}
                value={draftConfig.version}
                prefix="v"
                valueStyle={{ color: '#faad14' }}
              />
            )}
          </Col>
        </Row>
      </Card>

      {/* Threshold Configuration Form */}
      <Card title={t('superAdmin.thresholdConfig') || 'Threshold Configuration'}>
        <Alert
          type="info"
          message={t('superAdmin.safetyNote') || 'Safety Bounds'}
          description={`${t('superAdmin.safetyDesc') || 'Values must be within safety bounds:'} Systolic: ${safetyBounds.systolic_min}-${safetyBounds.systolic_max}, Diastolic: ${safetyBounds.diastolic_min}-${safetyBounds.diastolic_max}, Heart Rate: ${safetyBounds.heart_rate_min}-${safetyBounds.heart_rate_max}`}
          style={{ marginBottom: 24 }}
        />

        <Form form={form} layout="vertical">
          <Row gutter={24}>
            {/* Systolic Range */}
            <Col xs={24} md={8}>
              <Card size="small" title={t('superAdmin.systolic') || 'Systolic (mmHg)'} type="inner">
                <Form.Item
                  name="systolic_min"
                  label={t('superAdmin.min') || 'Min'}
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: safetyBounds.systolic_min, max: safetyBounds.systolic_max, message: `Must be ${safetyBounds.systolic_min}-${safetyBounds.systolic_max}` },
                  ]}
                >
                  <InputNumber style={{ width: '100%' }} min={safetyBounds.systolic_min} max={safetyBounds.systolic_max} />
                </Form.Item>
                <Form.Item
                  name="systolic_max"
                  label={t('superAdmin.max') || 'Max'}
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: safetyBounds.systolic_min, max: safetyBounds.systolic_max, message: `Must be ${safetyBounds.systolic_min}-${safetyBounds.systolic_max}` },
                  ]}
                >
                  <InputNumber style={{ width: '100%' }} min={safetyBounds.systolic_min} max={safetyBounds.systolic_max} />
                </Form.Item>
              </Card>
            </Col>

            {/* Diastolic Range */}
            <Col xs={24} md={8}>
              <Card size="small" title={t('superAdmin.diastolic') || 'Diastolic (mmHg)'} type="inner">
                <Form.Item
                  name="diastolic_min"
                  label={t('superAdmin.min') || 'Min'}
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: safetyBounds.diastolic_min, max: safetyBounds.diastolic_max, message: `Must be ${safetyBounds.diastolic_min}-${safetyBounds.diastolic_max}` },
                  ]}
                >
                  <InputNumber style={{ width: '100%' }} min={safetyBounds.diastolic_min} max={safetyBounds.diastolic_max} />
                </Form.Item>
                <Form.Item
                  name="diastolic_max"
                  label={t('superAdmin.max') || 'Max'}
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: safetyBounds.diastolic_min, max: safetyBounds.diastolic_max, message: `Must be ${safetyBounds.diastolic_min}-${safetyBounds.diastolic_max}` },
                  ]}
                >
                  <InputNumber style={{ width: '100%' }} min={safetyBounds.diastolic_min} max={safetyBounds.diastolic_max} />
                </Form.Item>
              </Card>
            </Col>

            {/* Heart Rate Range */}
            <Col xs={24} md={8}>
              <Card size="small" title={t('superAdmin.heartRate') || 'Heart Rate (bpm)'} type="inner">
                <Form.Item
                  name="heart_rate_min"
                  label={t('superAdmin.min') || 'Min'}
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: safetyBounds.heart_rate_min, max: safetyBounds.heart_rate_max, message: `Must be ${safetyBounds.heart_rate_min}-${safetyBounds.heart_rate_max}` },
                  ]}
                >
                  <InputNumber style={{ width: '100%' }} min={safetyBounds.heart_rate_min} max={safetyBounds.heart_rate_max} />
                </Form.Item>
                <Form.Item
                  name="heart_rate_max"
                  label={t('superAdmin.max') || 'Max'}
                  rules={[
                    { required: true, message: 'Required' },
                    { type: 'number', min: safetyBounds.heart_rate_min, max: safetyBounds.heart_rate_max, message: `Must be ${safetyBounds.heart_rate_min}-${safetyBounds.heart_rate_max}` },
                  ]}
                >
                  <InputNumber style={{ width: '100%' }} min={safetyBounds.heart_rate_min} max={safetyBounds.heart_rate_max} />
                </Form.Item>
              </Card>
            </Col>
          </Row>

          <Divider />

          {/* Action Buttons */}
          <Space wrap>
            <Button icon={<SaveOutlined />} onClick={handleSaveDraft} loading={saving}>
              {t('superAdmin.saveDraft') || 'Save as Draft'}
            </Button>
            <Button icon={<EyeOutlined />} onClick={handlePreview}>
              {t('superAdmin.preview') || 'Preview Impact'}
            </Button>
            <Button
              type="primary"
              icon={<CloudUploadOutlined />}
              onClick={handlePublish}
              loading={publishing}
              disabled={!draftConfig}
            >
              {t('superAdmin.publish') || 'Publish'}
            </Button>
            <Button icon={<ReloadOutlined />} onClick={handleReset}>
              {t('superAdmin.reset') || 'Reset to Default'}
            </Button>
          </Space>
        </Form>
      </Card>

      {/* Preview Modal */}
      <Modal
        open={showPreview}
        title={t('superAdmin.modals.previewTitle') || 'Impact Preview'}
        onCancel={() => setShowPreview(false)}
        footer={[
          <Button key="close" onClick={() => setShowPreview(false)}>
            {t('common.close') || 'Close'}
          </Button>,
        ]}
        width={500}
      >
        {previewData && (
          <div>
            <Alert
              type="info"
              message={t('superAdmin.previewNote') || 'Preview shows how existing records would be classified with the new thresholds.'}
              style={{ marginBottom: 16 }}
            />
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title={t('superAdmin.healthy') || 'Healthy'}
                  value={previewData.healthy}
                  suffix={`(${previewData.healthy_pct}%)`}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title={t('superAdmin.borderline') || 'Borderline'}
                  value={previewData.borderline}
                  suffix={`(${previewData.borderline_pct}%)`}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title={t('superAdmin.abnormal') || 'Abnormal'}
                  value={previewData.abnormal}
                  suffix={`(${previewData.abnormal_pct}%)`}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>
            <Divider />
            <Text type="secondary">
              {t('superAdmin.totalRecords') || 'Total records analyzed:'} {previewData.total}
            </Text>
          </div>
        )}
      </Modal>

      {/* Audit Logs Modal */}
      <Modal
        open={showAuditLogs}
        title={t('superAdmin.modals.auditTitle') || 'Audit Logs'}
        onCancel={() => setShowAuditLogs(false)}
        footer={[
          <Button key="export" icon={<DownloadOutlined />} onClick={handleExportAuditLogs}>
            {t('superAdmin.exportCsv') || 'Export CSV'}
          </Button>,
          <Button key="close" onClick={() => setShowAuditLogs(false)}>
            {t('common.close') || 'Close'}
          </Button>,
        ]}
        width={900}
      >
        <Table
          dataSource={auditLogs}
          columns={auditColumns}
          rowKey="id"
          size="small"
          scroll={{ x: 800 }}
          pagination={{ pageSize: 10 }}
        />
      </Modal>
    </div>
  );
};

export default SuperAdminSettings;
