import React from "react";
import { Link } from "react-router-dom";
import { Container, Button, Card, Row, Col } from "react-bootstrap";

const Home = () => {
  return (
    <Container className="mt-5">
      <div className="text-center mb-5">
        <h1 className="display-4 mb-3" style={{ color: '#C8102E', fontWeight: 'bold' }}>충북대학교 소왕이</h1>
        <p className="lead text-muted mb-4">
          학사일정, 공지사항, 소프트웨어학부 정보, 기숙사 정보를 AI로 빠르게 찾아보세요
        </p>
        <p className="text-muted" style={{ fontSize: '0.9em', marginBottom: '20px' }}>
          ⚠️ 위 정보는 100% 정확하지 않을 수 있습니다. 중요한 사항은 반드시 공식 홈페이지를 확인해주세요.
        </p>
        <Link to="/chat">
          <Button size="lg" className="me-3" style={{ backgroundColor: '#C8102E', borderColor: '#C8102E', color: '#fff' }}>
            💬 챗봇 시작하기
          </Button>
        </Link>
        <Link to="/calendar">
          <Button size="lg" style={{ backgroundColor: '#fff', borderColor: '#C8102E', color: '#C8102E' }}>
            📅 캘린더 보기
          </Button>
        </Link>
      </div>

      <Row className="mt-5">
        <Col md={3} className="mb-4">
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title style={{ color: '#C8102E' }}>📅 학사일정</Card.Title>
              <Card.Text>
                개강일, 종강일, 시험기간, 방학 등 학사일정을 빠르게 확인할 수 있습니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3} className="mb-4">
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title style={{ color: '#C8102E' }}>📢 공지사항</Card.Title>
              <Card.Text>
                학교 및 학과 공지사항을 AI가 분석하여 정확한 답변을 제공합니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3} className="mb-4">
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title style={{ color: '#C8102E' }}>💻 소프트웨어학부</Card.Title>
              <Card.Text>
                교수님, 연구실, 동아리, 졸업요건 등 소프트웨어학부 정보를 확인하세요.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3} className="mb-4">
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title style={{ color: '#C8102E' }}>🏠 기숙사 정보</Card.Title>
              <Card.Text>
                기숙사 연락처, 위치, 공지사항 등을 한 곳에서 확인하세요.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Home;
