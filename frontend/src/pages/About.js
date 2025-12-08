import React from "react";
import { Container, Card, Row, Col } from "react-bootstrap";

const About = () => {
  return (
    <Container className="mt-5">
      <h2 className="mb-4">서비스 소개</h2>
      
      <Card className="mb-4">
        <Card.Body>
          <Card.Title>충북대학교 공지사항 AI 챗봇</Card.Title>
          <Card.Text>
            충북대학교 학생들을 위한 AI 기반 공지사항 검색 및 질의응답 서비스입니다.
            자연어 처리와 검색 증강 생성(RAG) 기술을 활용하여 정확하고 빠른 정보 제공을 목표로 합니다.
          </Card.Text>
        </Card.Body>
      </Card>

      <h3 className="mb-3">주요 기술</h3>
      <Row className="mb-4">
        <Col md={6} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <Card.Title>🔍 벡터 검색</Card.Title>
              <Card.Text>
                PostgreSQL + pgvector를 활용한 의미론적 유사도 검색으로 
                키워드가 정확히 일치하지 않아도 관련 공지사항을 찾아냅니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <Card.Title>🤖 RAG 시스템</Card.Title>
              <Card.Text>
                검색 증강 생성(Retrieval-Augmented Generation) 기술로
                검색된 공지사항을 바탕으로 정확한 답변을 생성합니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <Card.Title>🧠 복잡도 감지</Card.Title>
              <Card.Text>
                질문의 복잡도를 자동으로 판단하여 단순 검색과 AI 분석을 
                적절히 선택해 빠르고 정확한 응답을 제공합니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6} className="mb-3">
          <Card className="h-100">
            <Card.Body>
              <Card.Title>🔄 자동 크롤링</Card.Title>
              <Card.Text>
                Scrapy 기반 자동 크롤링으로 충북대 공지사항을 
                주기적으로 수집하여 최신 정보를 유지합니다.
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <h3 className="mb-3">시스템 구조</h3>
      <Card className="mb-4">
        <Card.Body>
          <pre className="mb-0" style={{fontSize: '0.9rem'}}>
{`사용자 질문
    ↓
복잡도 감지 (단순 검색 / AI 분석)
    ↓
질문 임베딩 (768차원 벡터)
    ↓
pgvector 유사도 검색
    ↓
[단순] 구조화된 요약 반환
[복잡] LLM 생성 (컨텍스트 + 질문)
    ↓
답변 반환`}
          </pre>
        </Card.Body>
      </Card>

      <h3 className="mb-3">프로젝트 정보</h3>
      <Card>
        <Card.Body>
          <p><strong>프로젝트:</strong> 2025년 2학기 산학프로젝트</p>
          <p><strong>팀:</strong> SanHark Team</p>
          <p><strong>기술 스택:</strong></p>
          <ul>
            <li>Backend: Django, PostgreSQL, pgvector</li>
            <li>Frontend: React, Bootstrap</li>
            <li>AI: Ollama (LLaMA 3), Sentence Transformers</li>
            <li>Crawler: Scrapy</li>
          </ul>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default About;
