import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Space,
  Typography,
  Alert,
  Card,
  message,
  Form,
  InputNumber,
  Button,
  Row,
  Col,
  Skeleton,
  Modal,
  Table,
  Tag,
} from 'antd';
import dayjs from 'dayjs';
import localizedFormat from 'dayjs/plugin/localizedFormat';
import { useTranslation } from 'react-i18next';
import { getRoleFromToken } from '../utils/auth';
import { thresholdAPI } from '../services/api';

dayjs.extend(localizedFormat);

const DEFAULT_FORM_VALUES = {
  systolicLow: 90,
  systolicHigh: 120,
  diastolicLow: 60,
  diastolicHigh: 80,
  heartRateLow: 60,
  heartRateHigh: 90,
};

const deriveFormValues = (data) => {
  const nested = data?.thresholds || {};
  const payload = data?.profile || {};

  const systolicHealthy = nested?.systolic
    ? [nested.systolic.lower, nested.systolic.upper]
    : payload.systolic_healthy;
  const diastolicHealthy = nested?.diastolic
    ? [nested.diastolic.lower, nested.diastolic.upper]
    : payload.diastolic_healthy;
  const heartRateRange = nested?.heart_rate
    ? [nested.heart_rate.lower, nested.heart_rate.upper]
    : [payload.heart_rate_min, payload.heart_rate_max];

  return {
    systolicLow: systolicHealthy?.[0] ?? DEFAULT_FORM_VALUES.systolicLow,
    systolicHigh: systolicHealthy?.[1] ?? DEFAULT_FORM_VALUES.systolicHigh,
    diastolicLow: diastolicHealthy?.[0] ?? DEFAULT_FORM_VALUES.diastolicLow,
    diastolicHigh: diastolicHealthy?.[1] ?? DEFAULT_FORM_VALUES.diastolicHigh,
    heartRateLow: heartRateRange?.[0] ?? DEFAULT_FORM_VALUES.heartRateLow,
    heartRateHigh: heartRateRange?.[1] ?? DEFAULT_FORM_VALUES.heartRateHigh,
  };
};

const SuperAdminSettings = () => {
  const role = getRoleFromToken();
  const { t, i18n } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [metadata, setMetadata] = useState(null);
  const [initialValues, setInitialValues] = useState(DEFAULT_FORM_VALUES);
  const [draftId, setDraftId] = useState(null);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewData, setPreviewData] = useState([]);
  const [publishing, setPublishing] = useState(false);

  useEffect(() => {
    if (role !== 'SUPER_ADMIN') {
      message.error(t('admin.noAccess'));
    }
  }, [role, t]);

  const fetchThresholds = useCallback(async () => {
    if (role !== 'SUPER_ADMIN') return;
    setLoading(true);
    try {
      const { data } = await thresholdAPI.getActive();
      const derived = deriveFormValues(data);
      setInitialValues(derived);
      setMetadata({
        version: data?.version || null,
        updatedBy: data?.updated_by || '—',
        updatedAt: data?.updated_at || data?.effective_at || null,
      });
    } catch (error) {
      console.error('Failed to load thresholds', error);
      setInitialValues(DEFAULT_FORM_VALUES);
      message.warning(t('superAdmin.threshold.fetchError'));
    } finally {
      setLoading(false);
    }
  }, [role, t]);

  useEffect(() => {
    fetchThresholds();
  }, [fetchThresholds]);

  useEffect(() => {
    if (!loading) {
      form.setFieldsValue(initialValues);
    }
  }, [loading, initialValues, form]);

  const versionDescription = useMemo(() => {
    if (!metadata?.version) {
      return t('superAdmin.threshold.versionUnknown');
    }

    const formattedTime = metadata.updatedAt
      ? dayjs(metadata.updatedAt).locale(i18n.language.startsWith('en') ? 'en' : 'zh-cn').format('LLL')
      : '—';

    return `${t('superAdmin.threshold.versionLabel', { version: metadata.version })} · ${t('superAdmin.threshold.updated', {
      time: formattedTime,
      user: metadata.updatedBy || '—',
    })}`;
  }, [metadata, t, i18n.language]);

  const statusMap = useMemo(() => ({
    healthy: { color: 'green', text: t('threshold.status.healthy') },
    borderline: { color: 'orange', text: t('threshold.status.borderline') },
    out_of_range: { color: 'red', text: t('threshold.status.outOfRange') },
  }), [t]);

  const previewColumns = useMemo(() => ([
    {
      title: t('superAdmin.threshold.previewColumns.id'),
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: t('superAdmin.threshold.previewColumns.systolic'),
      dataIndex: 'systolic',
      key: 'systolic',
      width: 120,
      render: (value) => `${value} mmHg`,
    },
    {
      title: t('superAdmin.threshold.previewColumns.diastolic'),
      dataIndex: 'diastolic',
      key: 'diastolic',
      width: 120,
      render: (value) => `${value} mmHg`,
    },
    {
      title: t('superAdmin.threshold.previewColumns.heartRate'),
      dataIndex: 'heart_rate',
      key: 'heart_rate',
      width: 120,
      render: (value) => (value ? `${value} bpm` : '—'),
    },
    {
      title: t('superAdmin.threshold.previewColumns.status'),
      dataIndex: 'threshold_status',
      key: 'threshold_status',
      width: 140,
      render: (status) => {
        const config = statusMap[status] || { color: 'default', text: status };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: t('superAdmin.threshold.previewColumns.timestamp'),
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (value) => dayjs(value).locale(i18n.language.startsWith('en') ? 'en' : 'zh-cn').format('LLL'),
    },
  ]), [i18n.language, statusMap, t]);

  const loadPreview = useCallback(async (targetDraftId) => {
    if (!targetDraftId) {
      message.warning(t('superAdmin.threshold.previewNeedDraft'));
      return;
    }
    setPreviewLoading(true);
    try {
      const { data } = await thresholdAPI.preview(targetDraftId);
      setPreviewData(data?.preview || []);
      setPreviewVisible(true);
    } catch (error) {
      console.error('Failed to preview draft', error);
      message.error(t('superAdmin.threshold.previewError'));
    } finally {
      setPreviewLoading(false);
    }
  }, [t]);

  const handlePreview = async () => {
    await loadPreview(draftId);
  };

  const makeRangeRules = (type) => {
    const isHeartRate = type === 'heart';
    const min = 30;
    const max = isHeartRate ? 150 : 250;
    return [
      { required: true, message: t('superAdmin.threshold.required') },
      {
        validator: (_, value) => {
          if (value === undefined || value === null) return Promise.resolve();
          if (value < min || value > max) {
            return Promise.reject(new Error(t('superAdmin.threshold.validation.range')));
          }
          return Promise.resolve();
        },
      },
    ];
  };

  const createUpperRule = (lowerKey, type) => ({ getFieldValue }) => ({
    validator(_, value) {
      const lower = getFieldValue(lowerKey);
      if (value === undefined || value === null) {
        return Promise.resolve();
      }
      if (lower === undefined || lower === null) {
        return Promise.resolve();
      }
      if (value <= lower) {
        return Promise.reject(new Error(t('superAdmin.threshold.validation.order')));
      }
      const isHeartRate = type === 'heart';
      const min = 30;
      const max = isHeartRate ? 150 : 250;
      if (value < min || value > max) {
        return Promise.reject(new Error(t('superAdmin.threshold.validation.range')));
      }
      return Promise.resolve();
    },
  });

  const buildPayload = (values) => ({
    thresholds: {
      systolic: {
        lower: values.systolicLow,
        upper: values.systolicHigh,
      },
      diastolic: {
        lower: values.diastolicLow,
        upper: values.diastolicHigh,
      },
      heart_rate: {
        lower: values.heartRateLow,
        upper: values.heartRateHigh,
      },
    },
  });

  const handleSaveDraft = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      const response = await thresholdAPI.saveDraft(buildPayload(values));
      const newDraftId = response?.data?.id || null;
      setDraftId(newDraftId);
      message.success(t('superAdmin.threshold.saveSuccess'));
      if (newDraftId) {
        await loadPreview(newDraftId);
      }
    } catch (error) {
      if (error?.errorFields) {
        // validation errors already shown
        return;
      }
      console.error('Failed to save draft', error);
      message.error(t('superAdmin.threshold.saveError'));
    } finally {
      setSaving(false);
    }
  };

  const handlePublish = async () => {
    if (!draftId) {
      message.warning(t('superAdmin.threshold.publishNeedDraft'));
      return;
    }
    setPublishing(true);
    try {
      const { data } = await thresholdAPI.publish({ draft_id: draftId });
      const version = data?.version;
      message.success(t('superAdmin.threshold.publishSuccess', { version }));
      setPreviewVisible(false);
      setPreviewData([]);
      setDraftId(null);
      await fetchThresholds();
    } catch (error) {
      console.error('Failed to publish threshold', error);
      message.error(t('superAdmin.threshold.publishError'));
    } finally {
      setPublishing(false);
    }
  };

  if (role !== 'SUPER_ADMIN') {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={2}>{t('superAdmin.setting.title')}</Typography.Title>
      <Alert
        type="info"
        showIcon
        message={t('superAdmin.setting.subtitle')}
        description={t('superAdmin.setting.notice')}
      />

      <Card bordered={false} style={{ background: '#f7f9fc' }}>
        <Typography.Paragraph style={{ marginBottom: 0 }}>
          {t('superAdmin.threshold.description')}
        </Typography.Paragraph>
        <Typography.Text type={metadata?.version ? 'secondary' : 'warning'}>
          {versionDescription}
        </Typography.Text>
      </Card>

      <Card>
        {loading ? (
          <Skeleton active paragraph={{ rows: 6 }} />
        ) : (
          <Form layout="vertical" form={form} initialValues={DEFAULT_FORM_VALUES}>
            <Row gutter={[24, 24]}>
              <Col xs={24} md={12}>
                <Typography.Title level={4} style={{ marginTop: 0 }}>
                  {t('superAdmin.threshold.systolic')}
                </Typography.Title>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="systolicLow"
                      label={t('superAdmin.threshold.lower')}
                      rules={makeRangeRules('bp')}
                    >
                      <InputNumber min={30} max={250} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="systolicHigh"
                      label={t('superAdmin.threshold.upper')}
                      rules={[{ required: true, message: t('superAdmin.threshold.required') }, createUpperRule('systolicLow', 'bp')]}
                    >
                      <InputNumber min={30} max={250} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </Col>

              <Col xs={24} md={12}>
                <Typography.Title level={4} style={{ marginTop: 0 }}>
                  {t('superAdmin.threshold.diastolic')}
                </Typography.Title>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="diastolicLow"
                      label={t('superAdmin.threshold.lower')}
                      rules={makeRangeRules('bp')}
                    >
                      <InputNumber min={30} max={250} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="diastolicHigh"
                      label={t('superAdmin.threshold.upper')}
                      rules={[{ required: true, message: t('superAdmin.threshold.required') }, createUpperRule('diastolicLow', 'bp')]}
                    >
                      <InputNumber min={30} max={250} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </Col>

              <Col xs={24} md={12}>
                <Typography.Title level={4} style={{ marginTop: 0 }}>
                  {t('superAdmin.threshold.heartRate')}
                </Typography.Title>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item
                      name="heartRateLow"
                      label={t('superAdmin.threshold.lower')}
                      rules={makeRangeRules('heart')}
                    >
                      <InputNumber min={30} max={150} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item
                      name="heartRateHigh"
                      label={t('superAdmin.threshold.upper')}
                      rules={[{ required: true, message: t('superAdmin.threshold.required') }, createUpperRule('heartRateLow', 'heart')]}
                    >
                      <InputNumber min={30} max={150} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </Col>
            </Row>

            <Space size="middle" style={{ marginTop: 24 }}>
              <Button onClick={handlePreview} loading={previewLoading} disabled={!draftId && !previewData.length}>
                {t('superAdmin.threshold.preview')}
              </Button>
              <Button type="primary" loading={saving} onClick={handleSaveDraft}>
                {t('superAdmin.threshold.saveDraft')}
              </Button>
              <Button type="primary" ghost disabled={!draftId} loading={publishing} onClick={handlePublish}>
                {t('superAdmin.threshold.publish')}
              </Button>
            </Space>
          </Form>
        )}
      </Card>

      <Modal
        title={t('superAdmin.threshold.previewModalTitle')}
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        width={760}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            {t('common.close')}
          </Button>,
          <Button key="publish" type="primary" loading={publishing} onClick={handlePublish} disabled={!draftId}>
            {t('superAdmin.threshold.publish')}
          </Button>,
        ]}
      >
        <Table
          columns={previewColumns}
          dataSource={previewData}
          loading={previewLoading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Modal>

      <Typography.Paragraph type="secondary">
        {t('superAdmin.setting.placeholder')}
      </Typography.Paragraph>
    </Space>
  );
};

export default SuperAdminSettings;
