import React from "react";
import { Link } from "react-router-dom";
import { Container, Button, Card, Row, Col } from "react-bootstrap";

const Home = () => {
  return (
    <Container className="mt-5">
      <div className="text-center mb-5">
        <h1 className="display-4 mb-3">충북대학교 공지사항 챗봇</h1>
        <p className="lead text-muted mb-4">
          AI 기반 공지사항 검색 및 질의응답 서비스
        </p>
        <Link to="/chat">
          <Button variant="primary" size="lg" className="me-3">
            챗봇 시작하기
          </Button>
        </Link>
        <Link to="/about">
          <Button variant="outline-secondary" size="lg">
            서비스 소개
          </Button>
        </Link>
      </div>

      <Row className="mt-5">
        <Col md={4} className="mb-4">
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title>🔍 지능형 검색</Card.Title>
              <Card.Text>
                키워드 검색뿐만 아니라 자연어 질문으로 원하는 공지사항을 빠르게 찾을 수 있습니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4} className="mb-4">
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title>🤖 AI 분석</Card.Title>
              <Card.Text>
                복잡한 질문에 대해 AI가 공지사항을 분석하여 정확한 답변을 제공합니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4} className="mb-4">
          <Card className="h-100 shadow-sm">
            <Card.Body>
              <Card.Title>💬 대화형 인터페이스</Card.Title>
              <Card.Text>
                이전 대화를 기억하여 연속적인 질문에도 자연스럽게 답변합니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <div className="mt-5 p-4 bg-light rounded">
        <h3 className="mb-3">질문 예시</h3>
        <ul className="list-unstyled">
          <li className="mb-2">💡 "기숙사 신청 방법 알려줘"</li>
          <li className="mb-2">💡 "소프트웨어학과 졸업요건은 뭐야?"</li>
          <li className="mb-2">💡 "올해 취업공고에 뭐뭐 있는지 알려줘"</li>
          <li className="mb-2">💡 "장학금 관련 공지 찾아줘"</li>
        </ul>
      </div>
    </Container>
  );
};

export default Home;
