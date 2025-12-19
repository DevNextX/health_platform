import React from 'react';
import { Row, Col, Typography, Tag, Card, Divider } from 'antd';
import { useTranslation } from 'react-i18next';
import { HeartOutlined, DashboardOutlined } from '@ant-design/icons';

const { Text, Title } = Typography;

const HealthStandardsReference = ({ config }) => {
  const { t } = useTranslation();

  if (!config || !config.payload) {
    return null;
  }

  const { payload, version } = config;

  // Helper to extract ranges safely
  const getRanges = (metricKey) => {
    if (payload[metricKey] && typeof payload[metricKey] === 'object' && !Array.isArray(payload[metricKey])) {
      const { min, max, borderline_max } = payload[metricKey];
      return {
        healthy: `${min} - ${max}`,
        borderline: borderline_max ? `${max + 1} - ${borderline_max}` : null
      };
    }
    // Fallback for old format
    const healthyArr = payload[`${metricKey}_healthy`];
    const borderlineArr = payload[`${metricKey}_borderline`];
    return {
      healthy: healthyArr ? `${healthyArr[0]} - ${healthyArr[1]}` : '-',
      borderline: borderlineArr ? `${borderlineArr[0]} - ${borderlineArr[1]}` : null
    };
  };

  const systolic = getRanges('systolic');
  const diastolic = getRanges('diastolic');
  const heartRate = getRanges('heart_rate');

  return (
    <Card 
      style={{ marginBottom: 16 }}
      bodyStyle={{ padding: '16px 24px' }}
    >
      <Row align="middle" style={{ marginBottom: 12 }}>
        <DashboardOutlined style={{ fontSize: 18, marginRight: 8, color: '#1890ff' }} />
        <Title level={5} style={{ margin: 0, display: 'inline' }}>
          {t('threshold.reference.title', '健康阈值参考')}
        </Title>
        <Tag color="blue" style={{ marginLeft: 12 }}>v{version}</Tag>
      </Row>

      <Row gutter={[24, 16]}>
        {/* 血压部分 */}
        <Col xs={24} md={16}>
          <Text strong style={{ fontSize: 14, color: '#595959' }}>
            {t('threshold.reference.bloodPressure', '血压')} (mmHg)
          </Text>
          <Divider style={{ margin: '8px 0' }} />
          <Row gutter={[16, 12]}>
            <Col xs={24} sm={12}>
              <div style={{ padding: '8px 0' }}>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  {t('threshold.reference.systolic', '收缩压')}:
                </Text>
                <div style={{ marginTop: 6 }}>
                  <Tag color="green" style={{ marginBottom: 4 }}>
                    {t('threshold.status.healthy', '健康')}: {systolic.healthy}
                  </Tag>
                  {systolic.borderline && (
                    <Tag color="orange" style={{ marginBottom: 4 }}>
                      {t('threshold.status.borderline', '临界')}: {systolic.borderline}
                    </Tag>
                  )}
                </div>
              </div>
            </Col>
            <Col xs={24} sm={12}>
              <div style={{ padding: '8px 0' }}>
                <Text type="secondary" style={{ fontSize: 13 }}>
                  {t('threshold.reference.diastolic', '舒张压')}:
                </Text>
                <div style={{ marginTop: 6 }}>
                  <Tag color="green" style={{ marginBottom: 4 }}>
                    {t('threshold.status.healthy', '健康')}: {diastolic.healthy}
                  </Tag>
                  {diastolic.borderline && (
                    <Tag color="orange" style={{ marginBottom: 4 }}>
                      {t('threshold.status.borderline', '临界')}: {diastolic.borderline}
                    </Tag>
                  )}
                </div>
              </div>
            </Col>
          </Row>
        </Col>

        {/* 心率部分 */}
        <Col xs={24} md={8}>
          <Text strong style={{ fontSize: 14, color: '#595959' }}>
            <HeartOutlined style={{ marginRight: 6 }} />
            {t('threshold.reference.heartRate', '心率')} (bpm)
          </Text>
          <Divider style={{ margin: '8px 0' }} />
          <div style={{ padding: '8px 0' }}>
            <Tag color="green" style={{ marginBottom: 4 }}>
              {t('threshold.status.healthy', '健康')}: {heartRate.healthy}
            </Tag>
            {heartRate.borderline && (
              <Tag color="orange" style={{ marginBottom: 4 }}>
                {t('threshold.status.borderline', '临界')}: {heartRate.borderline}
              </Tag>
            )}
          </div>
        </Col>
      </Row>
    </Card>
  );
};

export default HealthStandardsReference;
