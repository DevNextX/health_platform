import React from 'react';
import { Alert, Steps, Typography, Divider } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title, Paragraph, Text } = Typography;

const FirstLoginGuide = () => {
  const { t } = useTranslation();
  return (
    <div>
      <Alert
        type="warning"
        showIcon
        message={t('firstLogin.alertTitle')}
        description={t('firstLogin.alertDesc')}
        style={{ marginBottom: 16 }}
      />
      <Steps
        direction="horizontal"
        current={1}
        items={[
          { title: t('firstLogin.steps.verify') },
          { title: t('firstLogin.steps.setPassword') },
          { title: t('firstLogin.steps.done') },
        ]}
        style={{ marginBottom: 16 }}
      />
      <Typography size="small">
        <Title level={5} style={{ marginTop: 0 }}>{t('firstLogin.tips.title')}</Title>
        <Paragraph style={{ marginBottom: 8 }}>
          - {t('firstLogin.tips.ruleLen')}
        </Paragraph>
        <Paragraph style={{ marginBottom: 8 }}>
          - {t('firstLogin.tips.ruleAvoid')}
        </Paragraph>
        <Paragraph style={{ marginBottom: 0 }}>
          - {t('firstLogin.tips.ruleAdmin')}
        </Paragraph>
      </Typography>
      <Divider style={{ margin: '16px 0' }} />
    </div>
  );
};

export default FirstLoginGuide;
