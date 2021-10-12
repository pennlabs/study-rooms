import React from 'react'

import Nav from './Nav'
import { Row, Col, Group } from '../styles/Layout'
import { MAX_BODY_HEIGHT } from '../styles/sizes'
import { Title, Text } from '../styles/Text'
import Wireframes from './Wireframes'

const LandingPage = () => {
  return (
    <>
      <Nav />
      <Row>
        <Col sm={12} md={12} lg={5} fullHeight padding="0 0 0 3rem">
          <Group style={{ marginTop: '6rem' }}>
            <Title>
              Welcome <br /> to Portal.
            </Title>
            <Text>ah, there will be some text here...</Text>
          </Group>
        </Col>
        <Col sm={12} md={12} lg={7} style={{ overflow: 'hidden' }}>
          <Wireframes />
        </Col>
      </Row>
    </>
  )
}

export default LandingPage
