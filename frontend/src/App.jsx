import React, { useState } from 'react';
import { Tent, Compass, Calendar, ShieldCheck, MapPin, Phone, MessageSquare, ChevronRight, CheckCircle2 } from 'lucide-react';
import ChatWidget from './components/ChatWidget';
import './App.css';

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const featuredItems = [
    {
      id: 1,
      name: "Tenda Dome 4P",
      desc: "Double layer waterproof, kapasitas 4 orang, termasuk pasak & frame fiber kuat.",
      price: "Rp 35.000 / hari",
      tag: "Best Seller"
    },
    {
      id: 2,
      name: "Carrier 60L Consina",
      desc: "Ergonomic backsystem, raincover include, nyaman untuk pendakian 3-4 hari.",
      price: "Rp 25.000 / hari",
      tag: "Populer"
    },
    {
      id: 3,
      name: "Paket Camping Hemat",
      desc: "1x Tenda 4P + 4x Matras Spons + 1x Kompor Portable + 1x Nesting DS-308.",
      price: "Rp 75.000 / hari",
      tag: "Paling Hemat"
    },
    {
      id: 4,
      name: "Sleeping Bag Polar",
      desc: "Bahan polar tebal, suhu kenyamanan 10-15°C, hangat untuk Gunung Merbabu/Prau.",
      price: "Rp 12.000 / hari",
      tag: "Wajib Bawa"
    }
  ];

  return (
    <div className="landing-wrapper">
      {/* Navbar */}
      <header className="navbar">
        <div className="nav-container">
          <div className="nav-logo">
            <div className="logo-badge">
              <Tent size={24} />
            </div>
            <div>
              <h1>Sabana Adventure</h1>
              <span className="logo-sub">Outdoor Gear Rental &bull; Jombor, Sleman</span>
            </div>
          </div>

          <div className="nav-actions">
            <a href="https://wa.me/6281234567890" target="_blank" rel="noreferrer" className="nav-wa-btn">
              <Phone size={16} />
              <span>WhatsApp Admin</span>
            </a>
            <button
              onClick={() => setIsChatOpen(true)}
              className="nav-chat-btn"
            >
              <MessageSquare size={16} />
              <span>Tanya AI Asisten</span>
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">
            <Compass size={16} />
            <span>Rental Alat Camping & Pendakian Terlengkap di Jogja</span>
          </div>
          <h2 className="hero-title">
            Jelajahi Alam Bebas Tanpa Repot Beli Perlengkapan Mahal
          </h2>
          <p className="hero-desc">
            Sewa tenda, carrier, kompor, dan perlengkapan gunung berkualitas di Sabana Adventure Jombor.
            Perhitungan sewa ramah kantong: sewa 3 hari hanya dihitung tarif 2 hari!
          </p>

          <div className="hero-cta-group">
            <button
              onClick={() => setIsChatOpen(true)}
              className="cta-primary"
            >
              <MessageSquare size={18} />
              <span>Cek Stok & Tanya AI Toko</span>
            </button>
            <a href="#katalog" className="cta-secondary">
              <span>Lihat Daftar Alat</span>
              <ChevronRight size={16} />
            </a>
          </div>

          <div className="hero-stats">
            <div className="stat-item">
              <strong>500+</strong>
              <span>Penyewa Aktif</span>
            </div>
            <div className="stat-separator" />
            <div className="stat-item">
              <strong>4.9/5</strong>
              <span>Rating Google</span>
            </div>
            <div className="stat-separator" />
            <div className="stat-item">
              <strong>100%</strong>
              <span>Alat Terawat & Bersih</span>
            </div>
          </div>
        </div>
      </section>

      {/* Keunggulan Toko */}
      <section className="features-section">
        <div className="section-header">
          <h3>Mengapa Sewa di Sabana Adventure?</h3>
          <p>Kemudahan dan transparansi untuk perjalanan outdoor terbaik kakak</p>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><Calendar size={24} /></div>
            <h4>Hitungan Sewa Fleksibel</h4>
            <p>Aturan sewa 3 hari cukup bayar 2 hari saja! Pengambilan H-1 sore hari tanpa biaya tambahan.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon"><ShieldCheck size={24} /></div>
            <h4>Syarat Mudah & Aman</h4>
            <p>Cukup jaminan KTP/SIM asli yang masih berlaku. Tanpa uang deposit ribet.</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon"><MapPin size={24} /></div>
            <h4>Lokasi Strategis</h4>
            <p>Dekat Terminal Jombor Sleman, sangat mudah dijangkau sebelum berangkat ke Merapi atau Merbabu.</p>
          </div>
        </div>
      </section>

      {/* Katalog Populer */}
      <section id="katalog" className="catalog-section">
        <div className="section-header">
          <h3>Katalog Alat Populer</h3>
          <p>Kualitas terawat, wangi, dan siap pakai mendaki</p>
        </div>

        <div className="catalog-grid">
          {featuredItems.map((item) => (
            <div key={item.id} className="catalog-card">
              <div className="catalog-tag">{item.tag}</div>
              <h4>{item.name}</h4>
              <p>{item.desc}</p>
              <div className="catalog-footer">
                <span className="price-tag">{item.price}</span>
                <button
                  onClick={() => setIsChatOpen(true)}
                  className="book-now-btn"
                >
                  Tanya AI
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-container">
          <p>&copy; 2026 Sabana Adventure Jombor. Capstone Project Team A26-CS204 (Gen AI).</p>
          <div className="footer-links">
            <span>Powered by FastAPI & Google Gemini RAG</span>
          </div>
        </div>
      </footer>

      {/* Tombol Melayang untuk Membuka Chat Widget */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="floating-chat-trigger"
          title="Tanya Asisten Toko"
        >
          <MessageSquare size={26} />
        </button>
      )}

      {/* Komponen Widget Chat */}
      <ChatWidget
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}
