import React from "react";
import { Link } from "react-router-dom";
import { Container, Button } from "react-bootstrap";

const Home = () => {
  return (
    <Container className="text-center mt-5">
      <h1 className="mb-3">홈 페이지</h1>
      <p className="lead mb-4">이곳은 챗봇 서비스 테스트 홈페이지입니다.</p>
      <Link to="/chat">
        <Button variant="primary" className="me-3">챗봇 페이지로 이동</Button>
      </Link>
      <Link to="/about">
        <Button variant="success">About Us</Button>
      </Link>
    </Container>
  );
};

export default Home;
