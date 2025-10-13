import React from "react";
import { Link } from "react-router-dom";

const Home = () => {
  return (
    <div>
      <h1>홈 페이지</h1>
      <p>챗봇 서비스 테스트</p>
      <Link to="/chat">
        <button>챗봇 페이지로 이동</button>
      </Link>
    </div>
  );
};

export default Home;
