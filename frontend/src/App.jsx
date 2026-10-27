import React, { useState, useEffect } from 'react';
import { 
  Tent, Compass, Search, ShoppingBag, Heart, User, Phone, 
  MessageSquare, ChevronLeft, ChevronRight, Star, Flame, 
  ShieldCheck, Clock, CheckCircle2, Tag, Filter, SlidersHorizontal
} from 'lucide-react';
import ChatWidget from './components/ChatWidget';
import './App.css';

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("semua");
  const [cartCount, setCartCount] = useState(0);
  const [currentSlide, setCurrentSlide] = useState(0);

  // Data Banner Promo Hero (Auto-slide horizontal)
  const promoBanners = [
    {
      id: 1,
      badge: "PROMO SPESIAL JOGJA",
      title: "Sewa 3 Hari Cuma Bayar 2 Hari!",
      subtitle: "Bebas denda ambil H-1 sore. Berlaku untuk semua perlengkapan gunung dan tenda camping.",
      cta: "Sewa Sekarang",
      bgGradient: "linear-gradient(135deg, #000000 0%, #1c1c16 60%, #2b2b10 100%)",
      accentTag: "Diskon 33% Otomatis"
    },
    {
      id: 2,
      badge: "PAKET BUNDLING HEMAT",
      title: "Paket Muncak Merbabu & Prau",
      subtitle: "Termasuk Tenda Dome 4P, 4x Matras Spons, Kompor Ultralight, dan Cooking Set Nesting.",
      cta: "Lihat Paket",
      bgGradient: "linear-gradient(135deg, #18181b 0%, #09090b 50%, #272710 100%)",
      accentTag: "Hanya Rp 75rb/hari"
    },
    {
      id: 3,
      badge: "JAMINAN KUALITAS",
      title: "Alat Bersih, Wangi, & Siap Badai",
      subtitle: "Double layer waterproof, frame fiber kuat, dan sleeping bag polar anti-dingin gunung.",
      cta: "Konsultasi ke AI",
      bgGradient: "linear-gradient(135deg, #0f172a 0%, #020617 60%, #1e293b 100%)",
      accentTag: "Garansi 100% Tukar"
    }
  ];

  // Auto-slide effect setiap 5 detik
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % promoBanners.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [promoBanners.length]);

  // Daftar Kategori E-Commerce
  const categories = [
    { id: "semua", label: "Semua Alat" },
    { id: "tenda", label: "Tenda & Shelter" },
    { id: "tas", label: "Carrier & Daypack" },
    { id: "tidur", label: "Matras & SB" },
    { id: "masak", label: "Alat Masak & Gas" },
    { id: "penerangan", label: "Headlamp & Lampu" },
    { id: "alas_kaki", label: "Sepatu Hiking" },
    { id: "aksesori", label: "Kursi & Trekking Pole" }
  ];

  // Data Katalog Produk Lengkap Sabana Adventure
  const catalogProducts = [
    {
      id: "TND-DOME-4",
      name: "Tenda Dome Kapasitas 4P",
      category: "tenda",
      price: 35000,
      rating: 4.9,
      rentCount: 284,
      desc: "Double layer waterproof, pasak & frame kokoh, ventilasi atas anti-kondensasi.",
      badge: "Paling Laris",
      stock: 6
    },
    {
      id: "TND-DOME-2",
      name: "Tenda Dome Kapasitas 2P",
      category: "tenda",
      price: 25000,
      rating: 4.8,
      rentCount: 156,
      desc: "Ringan dan praktis untuk solo trip atau berdua, pasak baja ringan.",
      badge: "Best Value",
      stock: 6
    },
    {
      id: "TND-DOME-6",
      name: "Tenda Dome Kapasitas 6P",
      category: "tenda",
      price: 50000,
      rating: 4.9,
      rentCount: 98,
      desc: "Keluarga/rombongan, ruang vestibule luas untuk taruh barang dan masak.",
      badge: "Keluarga",
      stock: 4
    },
    {
      id: "CRR-60L",
      name: "Carrier Consina 60L",
      category: "tas",
      price: 25000,
      rating: 4.9,
      rentCount: 210,
      desc: "Ergonomic backsystem busa tebal, sirkulasi udara punggung, include raincover.",
      badge: "Favorit",
      stock: 8
    },
    {
      id: "CRR-80L",
      name: "Carrier Ekspedisi 80L",
      category: "tas",
      price: 30000,
      rating: 4.8,
      rentCount: 65,
      desc: "Kapasitas raksasa untuk pendakian panjang (Semeru, Rinjani), frame ganda.",
      badge: "Ekspedisi",
      stock: 3
    },
    {
      id: "SLB-POLAR",
      name: "Sleeping Bag Polar Tebal",
      category: "tidur",
      price: 12000,
      rating: 4.9,
      rentCount: 340,
      desc: "Lapisan polar tebal, suhu kenyamanan 8-15°C, wangi dan bersih dicuci tiap sewa.",
      badge: "Wajib Bawa",
      stock: 10
    },
    {
      id: "MTR-SPONS",
      name: "Matras Spons Tebal Gulung",
      category: "tidur",
      price: 5000,
      rating: 4.7,
      rentCount: 420,
      desc: "Alas tidur anti-dingin tanah, tidak mudah robek, tali pengikat praktis.",
      badge: "Ekonomis",
      stock: 20
    },
    {
      id: "STV-PORT",
      name: "Kompor Portable Windproof",
      category: "masak",
      price: 8000,
      rating: 4.9,
      rentCount: 310,
      desc: "Bisa dilipat compact, penahan angin tipe bunga, pemantik elektrik otomatis.",
      badge: "Praktis",
      stock: 10
    },
    {
      id: "NST-SET",
      name: "Cooking Set Nesting DS-308",
      category: "masak",
      price: 8000,
      rating: 4.8,
      rentCount: 275,
      desc: "Panci ganda + wajan aluminium tebal teflon, mangkok kecil & spons cuci.",
      badge: "Lengkap",
      stock: 10
    },
    {
      id: "HDL-STD",
      name: "Headlamp LED Cree 300 Lumens",
      category: "penerangan",
      price: 8000,
      rating: 4.9,
      rentCount: 190,
      desc: "Mode terang, redup, & SOS merah. Tali elastis nyaman, baterai tahan 10 jam.",
      badge: "Safety",
      stock: 15
    },
    {
      id: "SPT-HIK",
      name: "Sepatu Gunung Trekking",
      category: "alas_kaki",
      price: 20000,
      rating: 4.8,
      rentCount: 140,
      desc: "Outsole vibram anti-slip licin tanah basah, ankle support pelindung mata kaki.",
      badge: "Safety",
      stock: 10
    },
    {
      id: "KRS-LPT",
      name: "Kursi Lipat Camping Portabel",
      category: "aksesori",
      price: 8000,
      rating: 4.9,
      rentCount: 220,
      desc: "Rangka pipa besi kuat beban 100kg, bahan oxford tebal, kantong cangkir.",
      badge: "Santai",
      stock: 8
    }
  ];

  // Filter produk berdasarkan kategori dan pencarian
  const filteredProducts = catalogProducts.filter((product) => {
    const matchCategory = selectedCategory === "semua" || product.category === selectedCategory;
    const matchSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        product.desc.toLowerCase().includes(searchQuery.toLowerCase());
    return matchCategory && matchSearch;
  });

  const handleAddToCart = (productName) => {
    setCartCount(prev => prev + 1);
  };

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(num);
  };

  return (
    <div className="ecommerce-wrapper">
      {/* 1. TOP ANNOUNCEMENT BAR */}
      <div className="top-bar">
        <div className="top-bar-inner">
          <div className="top-bar-info">
            <span className="top-tag">SABANA PROMO</span>
            <span>Aturan Sewa: Sewa 3 hari dihitung tarif 2 hari &bull; Ambil H-1 Sore Tanpa Biaya Tambahan!</span>
          </div>
          <div className="top-bar-links">
            <a href="https://wa.me/6281234567890" target="_blank" rel="noreferrer" className="top-link">
              <Phone size={13} /> CS WhatsApp: 0812-3456-7890
            </a>
            <span className="top-sep">|</span>
            <span className="top-loc">Lokasi: Jombor, Sleman (Dekat Flyover)</span>
          </div>
        </div>
      </div>

      {/* 2. E-COMMERCE MAIN NAVBAR */}
      <header className="main-header">
        <div className="header-inner">
          {/* Logo Brand */}
          <div className="brand-logo" onClick={() => setSelectedCategory("semua")}>
            <div className="brand-icon">
              <Tent size={24} />
            </div>
            <div className="brand-text">
              <h2>SABANA</h2>
              <span>ADVENTURE &bull; OUTDOOR GEAR</span>
            </div>
          </div>

          {/* Search Bar Platform E-commerce */}
          <div className="search-box-wrapper">
            <div className="search-box">
              <Search size={18} className="search-icon" />
              <input
                type="text"
                placeholder="Cari tenda dome 4p, carrier 60L, kompor, sleeping bag..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button className="clear-search" onClick={() => setSearchQuery("")}>&times;</button>
              )}
            </div>
          </div>

          {/* User & Cart Actions */}
          <div className="header-actions">
            {/* Tombol Tanya AI Asisten */}
            <button
              onClick={() => setIsChatOpen(true)}
              className="ai-chat-nav-btn"
              title="Konsultasi Alat & Cek Sewa dengan AI"
            >
              <MessageSquare size={17} />
              <span className="btn-label">Tanya AI</span>
            </button>

            {/* Keranjang Sewa */}
            <div className="cart-action-btn" onClick={() => setIsChatOpen(true)} title="Daftar Alat Disewa">
              <ShoppingBag size={20} />
              {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
              <span className="btn-label-cart">Keranjang</span>
            </div>
          </div>
        </div>

        {/* 3. CATEGORY BAR HORIZONTAL */}
        <nav className="category-navbar">
          <div className="category-scroll">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`category-nav-btn ${selectedCategory === cat.id ? 'active' : ''}`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </nav>
      </header>

      {/* 4. HERO PROMO BANNER (ANIMASI SLIDE HORISONTAL OTOMATIS) */}
      <section className="hero-banner-section">
        <div className="banner-slider-container">
          <div 
            className="banner-slider-track"
            style={{ transform: `translateX(-${currentSlide * 100}%)` }}
          >
            {promoBanners.map((banner) => (
              <div 
                key={banner.id} 
                className="banner-slide"
                style={{ background: banner.bgGradient }}
              >
                <div className="slide-content">
                  <div className="slide-badge-row">
                    <span className="slide-badge">{banner.badge}</span>
                    <span className="slide-accent-tag">{banner.accentTag}</span>
                  </div>
                  <h1 className="slide-title">{banner.title}</h1>
                  <p className="slide-subtitle">{banner.subtitle}</p>
                  
                  <div className="slide-actions">
                    <a href="#katalog-grid" className="slide-cta-btn">
                      {banner.cta}
                    </a>
                    <button 
                      onClick={() => setIsChatOpen(true)}
                      className="slide-ai-btn"
                    >
                      <MessageSquare size={16} />
                      Tanya Asisten Toko
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Slider Navigation Buttons */}
          <button 
            className="slider-arrow arrow-prev"
            onClick={() => setCurrentSlide((prev) => (prev === 0 ? promoBanners.length - 1 : prev - 1))}
            aria-label="Slide Sebelumnya"
          >
            <ChevronLeft size={22} />
          </button>
          <button 
            className="slider-arrow arrow-next"
            onClick={() => setCurrentSlide((prev) => (prev + 1) % promoBanners.length)}
            aria-label="Slide Selanjutnya"
          >
            <ChevronRight size={22} />
          </button>

          {/* Slider Dots */}
          <div className="slider-dots">
            {promoBanners.map((_, idx) => (
              <span
                key={idx}
                className={`dot-indicator ${currentSlide === idx ? 'active' : ''}`}
                onClick={() => setCurrentSlide(idx)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* 5. BRANDING VALUE STRIP (KEUNGGULAN E-COMMERCE TOKO) */}
      <section className="trust-strip">
        <div className="trust-inner">
          <div className="trust-card">
            <div className="trust-icon"><ShieldCheck size={22} /></div>
            <div>
              <h4>Syarat & Jaminan Mudah</h4>
              <p>Cukup KTP/SIM asli tanpa deposit ribet</p>
            </div>
          </div>
          <div className="trust-card">
            <div className="trust-icon"><Clock size={22} /></div>
            <div>
              <h4>Sewa 3 Hari Bayar 2 Hari</h4>
              <p>Kalkulasi hemat ramah kantong mahasiswa</p>
            </div>
          </div>
          <div className="trust-card">
            <div className="trust-icon"><CheckCircle2 size={22} /></div>
            <div>
              <h4>Alat Bersih & Steril</h4>
              <p>Dicuci bersih dan dicek sebelum diserahkan</p>
            </div>
          </div>
          <div className="trust-card">
            <div className="trust-icon"><Flame size={22} /></div>
            <div>
              <h4>Bebas Booking Tanpa DP</h4>
              <p>Pesan lewat web chat atau WhatsApp</p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. KATALOG PRODUK UTAMA */}
      <main id="katalog-grid" className="catalog-section">
        <div className="catalog-container">
          {/* Header Katalog */}
          <div className="catalog-header-row">
            <div>
              <h2 className="catalog-heading">Katalog Alat Camping Sabana</h2>
              <p className="catalog-sub">
                Menampilkan <b>{filteredProducts.length}</b> peralatan siap sewa di Jombor, Sleman
              </p>
            </div>

            <div className="catalog-filter-info">
              <span className="active-filter-badge">
                <Tag size={13} /> {categories.find(c => c.id === selectedCategory)?.label}
              </span>
            </div>
          </div>

          {/* Grid Kartu Produk E-Commerce */}
          {filteredProducts.length === 0 ? (
            <div className="empty-catalog">
              <p>Tidak ditemukan alat dengan kata kunci "<b>{searchQuery}</b>"</p>
              <button onClick={() => { setSearchQuery(""); setSelectedCategory("semua"); }} className="reset-btn">
                Tampilkan Semua Alat
              </button>
            </div>
          ) : (
            <div className="products-grid">
              {filteredProducts.map((item) => (
                <div key={item.id} className="product-card">
                  {/* Badge Atas */}
                  <div className="card-top-badge">
                    <span className="badge-tag">{item.badge}</span>
                    <span className="stock-info">Stok: {item.stock}</span>
                  </div>

                  {/* Thumbnail / Ilustrasi Visual Produk */}
                  <div className="card-thumbnail">
                    <Tent size={48} className="thumb-icon" />
                    <span className="thumb-cat">{item.category.toUpperCase()}</span>
                  </div>

                  {/* Detail Info Produk */}
                  <div className="card-body">
                    <div className="card-rating">
                      <Star size={14} className="star-filled" />
                      <span>{item.rating}</span>
                      <span className="rent-count">&bull; {item.rentCount}x disewa</span>
                    </div>

                    <h3 className="product-title">{item.name}</h3>
                    <p className="product-desc">{item.desc}</p>

                    <div className="card-price-row">
                      <div>
                        <span className="price-prefix">Tarif Sewa:</span>
                        <div className="price-value">{formatRupiah(item.price)} <span className="price-unit">/ hari</span></div>
                      </div>
                    </div>

                    {/* Tombol Sewa & Tanya AI */}
                    <div className="card-btn-group">
                      <button 
                        onClick={() => handleAddToCart(item.name)}
                        className="btn-rent"
                      >
                        + Sewa
                      </button>
                      <button 
                        onClick={() => setIsChatOpen(true)}
                        className="btn-ask-ai"
                        title="Tanya ketersediaan atau spek alat ini"
                      >
                        <MessageSquare size={15} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* 7. FOOTER E-COMMERCE */}
      <footer className="main-footer">
        <div className="footer-content">
          <div className="footer-col">
            <div className="footer-brand">
              <Tent size={24} />
              <h3>Sabana Adventure</h3>
            </div>
            <p className="footer-desc">
              Pusat persewaan alat outdoor, camping, dan pendakian gunung terlengkap di Jombor, Sleman, Yogyakarta.
            </p>
            <div className="footer-info-item">
              <Phone size={15} />
              <span>WhatsApp Admin: 0812-3456-7890</span>
            </div>
          </div>

          <div className="footer-col">
            <h4>Kebijakan & Syarat Sewa</h4>
            <ul>
              <li>Sewa 3 hari dihitung tarif 2 hari</li>
              <li>Jaminan fisik KTP / SIM asli berlaku</li>
              <li>Pengambilan barang H-1 sore hari</li>
              <li>Wajib konfirmasi sebelum pengembalian</li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>Didukung Teknologi Gen AI</h4>
            <p className="footer-desc">
              Asisten virtual pintar berbasis Retrieval-Augmented Generation (RAG) untuk menjawab pertanyaan seputar katalog dan menghitung tarif sewa otomatis.
            </p>
            <button onClick={() => setIsChatOpen(true)} className="footer-chat-btn">
              <MessageSquare size={16} /> Buka Chat AI Asisten
            </button>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 Sabana Adventure Jombor. Tim A26-CS204 Capstone Project Gen AI.</p>
        </div>
      </footer>

      {/* 8. TOMBOL TRIGGER WIDGET CHAT MELAYANG */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="floating-chat-trigger"
          title="Tanya Asisten Toko Sabana"
        >
          <MessageSquare size={26} />
        </button>
      )}

      {/* 9. KOMPONEN WIDGET CHAT AI */}
      <ChatWidget
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}
