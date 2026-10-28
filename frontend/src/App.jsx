import React, { useState, useEffect, useRef } from 'react';
import { 
  Tent, Compass, Search, ShoppingBag, Heart, User, Phone, 
  MessageSquare, ChevronLeft, ChevronRight, Star, Flame, 
  ShieldCheck, Clock, CheckCircle2, Tag, Filter, Sparkles,
  ArrowRight, Shield, Zap, ThumbsUp, PackageCheck, X, Trash2,
  Plus, Minus, ShoppingCart, Send, MapPin, Award
} from 'lucide-react';
import ChatWidget from './components/ChatWidget';
import './App.css';

// Komponen Ikon Media Sosial Resmi Sabana Adventure
const TikTokIcon = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64c.298-.002.595.042.88.13V9.4a6.33 6.33 0 0 0-1-.08A6.34 6.34 0 0 0 3 15.66a6.34 6.34 0 0 0 10.78 4.49 6.27 6.27 0 0 0 1.9-4.48V8.55a8.29 8.29 0 0 0 4.79 1.54V6.69z"/>
  </svg>
);

const InstagramIcon = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5"/>
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/>
  </svg>
);

const WhatsAppIcon = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.05 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
);

const FacebookIcon = ({ size = 17 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
  </svg>
);

// Helper render ikon produk berdasarkan kategori
const renderProductIcon = (category) => {
  switch (category) {
    case 'tenda': return <Tent size={46} className="shopee-preview-icon" />;
    case 'tas': return <ShoppingBag size={46} className="shopee-preview-icon" />;
    case 'masak': return <Flame size={46} className="shopee-preview-icon" />;
    case 'tidur': return <ShieldCheck size={46} className="shopee-preview-icon" />;
    case 'penerangan': return <Zap size={46} className="shopee-preview-icon" />;
    case 'alas_kaki': return <Compass size={46} className="shopee-preview-icon" />;
    default: return <Tent size={46} className="shopee-preview-icon" />;
  }
};

export default function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [cartItems, setCartItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("semua");
  const [currentSlide, setCurrentSlide] = useState(0);
  const catalogScrollRef = useRef(null);

  // Data Banner Promo Hero (Auto-slide horizontal)
  const promoBanners = [
    {
      id: 1,
      badge: "PROMO SPESIAL JOGJA",
      title: "Sewa 3 Hari Cuma Bayar 2 Hari!",
      subtitle: "Bebas denda ambil H-1 sore. Berlaku untuk semua perlengkapan gunung dan tenda camping.",
      cta: "Jelajahi Katalog",
      bgGradient: "linear-gradient(135deg, #000000 0%, #1c1c16 60%, #2b2b10 100%)",
      accentTag: "Diskon 33% Otomatis"
    },
    {
      id: 2,
      badge: "PAKET BUNDLING HEMAT",
      title: "Paket Muncak Merbabu & Prau",
      subtitle: "Termasuk Tenda Dome 4P, 4x Matras Spons, Kompor Ultralight, dan Cooking Set Nesting.",
      cta: "Lihat Produk",
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
      accentTag: "Garansi 100% Siap Pakai"
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
    { id: "tas", label: "Carrier & Tas" },
    { id: "tidur", label: "Matras & SB" },
    { id: "masak", label: "Kompor & Nesting" },
    { id: "penerangan", label: "Headlamp & Lampu" },
    { id: "alas_kaki", label: "Sepatu Hiking" },
    { id: "aksesori", label: "Kursi & Alat Camp" }
  ];

  // Data Katalog Produk Sabana Adventure (Shopee/Tokopedia outdoor style)
  const catalogProducts = [
    {
      id: "TND-DOME-4",
      name: "Tenda Dome Kapasitas 4 Orang Waterproof Double Layer",
      category: "tenda",
      price: 35000,
      originalPrice: 45000,
      rating: 4.9,
      soldCount: 482,
      location: "Sleman, DIY",
      badge: "Star+",
      stock: 6,
      tags: ["Double Layer", "Alas Terpal", "Frame Fiber"]
    },
    {
      id: "TND-DOME-2",
      name: "Tenda Dome Kapasitas 2 Orang Ultralight Praktis",
      category: "tenda",
      price: 25000,
      originalPrice: 30000,
      rating: 4.8,
      soldCount: 230,
      location: "Sleman, DIY",
      badge: "Diskon 17%",
      stock: 6,
      tags: ["Solo Camp", "Waterproof 2000mm"]
    },
    {
      id: "TND-DOME-6",
      name: "Tenda Dome Kapasitas 6 Orang Family Camping Besar",
      category: "tenda",
      price: 50000,
      originalPrice: 65000,
      rating: 4.9,
      soldCount: 114,
      location: "Sleman, DIY",
      badge: "Keluarga",
      stock: 4,
      tags: ["Vestibule Luas", "Ventilasi Anti Pengap"]
    },
    {
      id: "CRR-60L",
      name: "Carrier Consina 60L Ergonomic Backsystem + Raincover",
      category: "tas",
      price: 25000,
      originalPrice: 35000,
      rating: 4.9,
      soldCount: 395,
      location: "Sleman, DIY",
      badge: "Star+",
      stock: 8,
      tags: ["Free Raincover", "Busa Tebal"]
    },
    {
      id: "CRR-80L",
      name: "Tas Carrier Ekspedisi 80L Heavy Duty Pendakian Jauh",
      category: "tas",
      price: 30000,
      originalPrice: 40000,
      rating: 4.8,
      soldCount: 88,
      location: "Sleman, DIY",
      badge: "Ekspedisi",
      stock: 3,
      tags: ["Double Frame Baja", "Torso Adjustable"]
    },
    {
      id: "SLB-POLAR",
      name: "Sleeping Bag Bulu Polar Tebal Anti Dingin Suhu 10°C",
      category: "tidur",
      price: 12000,
      originalPrice: 15000,
      rating: 4.9,
      soldCount: 650,
      location: "Sleman, DIY",
      badge: "Terlaris",
      stock: 10,
      tags: ["Wangi & Bersih", "Hangat Merbabu"]
    },
    {
      id: "MTR-SPONS",
      name: "Matras Spons Tebal Gulung Alas Tidur Tenda Camping",
      category: "tidur",
      price: 5000,
      originalPrice: 7000,
      rating: 4.7,
      soldCount: 812,
      location: "Sleman, DIY",
      badge: "Termurah",
      stock: 20,
      tags: ["Tebal 4mm", "Anti Lembap"]
    },
    {
      id: "STV-PORT",
      name: "Kompor Portable Camping Windproof Model Bunga Anti Angin",
      category: "masak",
      price: 8000,
      originalPrice: 12000,
      rating: 4.9,
      soldCount: 520,
      location: "Sleman, DIY",
      badge: "Star+",
      stock: 10,
      tags: ["Pemantik Otomatis", "Lipat Kompak"]
    },
    {
      id: "NST-SET",
      name: "Cooking Set Nesting DS-308 Panci Wajan Teflon Camping",
      category: "masak",
      price: 8000,
      originalPrice: 12000,
      rating: 4.8,
      soldCount: 410,
      location: "Sleman, DIY",
      badge: "Lengkap",
      stock: 10,
      tags: ["Anti Lengket", "Include Spons Cuci"]
    },
    {
      id: "HDL-STD",
      name: "Headlamp LED Cree 300 Lumens Senter Kepala Outdoor",
      category: "penerangan",
      price: 8000,
      originalPrice: 10000,
      rating: 4.9,
      soldCount: 290,
      location: "Sleman, DIY",
      badge: "Safety",
      stock: 15,
      tags: ["3 Mode Lampu", "Tali Elastis"]
    },
    {
      id: "SPT-HIK",
      name: "Sepatu Gunung Hiking Trekking Grip Vibram Anti Slip",
      category: "alas_kaki",
      price: 20000,
      originalPrice: 28000,
      rating: 4.8,
      soldCount: 175,
      location: "Sleman, DIY",
      badge: "Safety",
      stock: 10,
      tags: ["Ankle Support", "Water Resistant"]
    },
    {
      id: "KRS-LPT",
      name: "Kursi Lipat Camping Portabel Rangka Besi Kuat Beban 100kg",
      category: "aksesori",
      price: 8000,
      originalPrice: 12000,
      rating: 4.9,
      soldCount: 360,
      location: "Sleman, DIY",
      badge: "Santai",
      stock: 8,
      tags: ["Ada Cup Holder", "Ringan Dibawa"]
    }
  ];

  // Filter produk berdasarkan kategori dan pencarian
  const filteredProducts = catalogProducts.filter((product) => {
    const matchCategory = selectedCategory === "semua" || product.category === selectedCategory;
    const matchSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        product.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchCategory && matchSearch;
  });

  // Manajemen Keranjang Sewa
  const handleAddToCart = (product) => {
    setCartItems(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item => item.id === product.id ? { ...item, qty: item.qty + 1 } : item);
      }
      return [...prev, { ...product, qty: 1 }];
    });
    setIsCartOpen(true);
  };

  const updateCartQty = (id, delta) => {
    setCartItems(prev => prev.map(item => {
      if (item.id === id) {
        const newQty = item.qty + delta;
        return newQty > 0 ? { ...item, qty: newQty } : null;
      }
      return item;
    }).filter(Boolean));
  };

  const removeCartItem = (id) => {
    setCartItems(prev => prev.filter(item => item.id !== id));
  };

  const totalCartCount = cartItems.reduce((acc, curr) => acc + curr.qty, 0);
  const totalCartPrice = cartItems.reduce((acc, curr) => acc + (curr.price * curr.qty), 0);

  const formatRupiah = (num) => {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(num);
  };

  // Navigasi scroll horizontal katalog
  const scrollCatalog = (direction) => {
    if (catalogScrollRef.current) {
      const scrollAmount = 340;
      catalogScrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="ecommerce-wrapper">
      {/* 1. TOP ANNOUNCEMENT BAR (COMPACT & BALANCED) */}
      <div className="top-bar">
        <div className="top-bar-inner">
          <div className="top-bar-info">
            <span className="top-tag">PROMO</span>
            <span className="top-bar-promo-text">Sewa 3 Hari Bayar 2 Hari &bull; Bebas Biaya H-1</span>
          </div>
          <div className="top-bar-links">
            <a href="https://wa.me/6281234567890" target="_blank" rel="noreferrer" className="top-link">
              <Phone size={12} /> CS WA: 0812-3456-7890
            </a>
            <span className="top-sep">&bull;</span>
            <span className="top-loc">Jombor, Sleman</span>
          </div>
        </div>
      </div>

      {/* 2. E-COMMERCE MAIN NAVBAR (HANYA TOMBOL KERANJANG, TANPA TOMBOL TANYA AI) */}
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

          {/* User & Cart Actions (Hanya Keranjang Produk - Tanpa Label Nominal Rp 0) */}
          <div className="header-actions">
            <div 
              className="cart-action-btn" 
              onClick={() => setIsCartOpen(true)} 
              title="Buka Keranjang Sewa"
              role="button"
              tabIndex={0}
            >
              <div className="cart-icon-wrapper">
                <ShoppingCart size={21} />
                {totalCartCount > 0 && <span className="cart-badge">{totalCartCount}</span>}
              </div>
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
                    <a href="#katalog-horizontal" className="slide-cta-btn">
                      {banner.cta}
                    </a>
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

      {/* 5. BRANDING & VALUE STRIP (MINIMALIS & RAMPING) */}
      <section className="trust-strip-modern">
        <div className="trust-strip-container">
          <div className="trust-item">
            <div className="trust-pill-icon"><Shield size={18} /></div>
            <div className="trust-text-group">
              <span className="trust-headline">Syarat & Jaminan Mudah</span>
              <span className="trust-subline">Cukup KTP/SIM asli tanpa deposit ribet</span>
            </div>
          </div>

          <div className="trust-divider" />

          <div className="trust-item">
            <div className="trust-pill-icon highlight"><Zap size={18} /></div>
            <div className="trust-text-group">
              <span className="trust-headline">Sewa 3 Hari Bayar 2 Hari</span>
              <span className="trust-subline">Kalkulasi hemat ramah kantong mahasiswa</span>
            </div>
          </div>

          <div className="trust-divider" />

          <div className="trust-item">
            <div className="trust-pill-icon"><PackageCheck size={18} /></div>
            <div className="trust-text-group">
              <span className="trust-headline">Alat Bersih & Steril</span>
              <span className="trust-subline">Dicuci bersih & dicek sebelum diserahkan</span>
            </div>
          </div>

          <div className="trust-divider" />

          <div className="trust-item">
            <div className="trust-pill-icon"><ThumbsUp size={18} /></div>
            <div className="trust-text-group">
              <span className="trust-headline">Bebas Booking Tanpa DP</span>
              <span className="trust-subline">Pesan cepat via web chat atau WhatsApp</span>
            </div>
          </div>
        </div>
      </section>

      {/* 6. KATALOG PRODUK UTAMA (SHOPEE-INSPIRED CLEAN OUTDOOR CARDS) */}
      <main id="katalog-horizontal" className="catalog-section">
        <div className="catalog-container">
          {/* Header Bar Katalog */}
          <div className="catalog-header-bar">
            <div className="catalog-title-area">
              <div className="catalog-badge-pill">
                <Flame size={14} /> KATALOG SEWA SABANA
              </div>
              <h2 className="catalog-main-title">Rekomendasi Alat Camping Pilihan</h2>
              <p className="catalog-sub-title">
                {filteredProducts.length >= 6 ? (
                  <>Geser ke kanan untuk melihat seluruh alat &bull; Tersedia <b>{filteredProducts.length}</b> peralatan</>
                ) : (
                  <>Tersedia <b>{filteredProducts.length}</b> peralatan pilihan siap sewa</>
                )}
              </p>
            </div>
          </div>

          {/* Wrapper Slider Horizontal dengan Tombol Melayang Samping (Hanya jika >= 6 barang) */}
          <div className="catalog-slider-wrapper">
            {filteredProducts.length >= 6 && (
              <button 
                onClick={() => scrollCatalog('left')}
                className="catalog-floating-arrow arrow-left"
                aria-label="Geser ke kiri"
                title="Geser ke kiri"
              >
                <ChevronLeft size={24} strokeWidth={2.5} />
              </button>
            )}

            {filteredProducts.length === 0 ? (
              <div className="empty-catalog">
                <p>Tidak ditemukan alat dengan kata kunci "<b>{searchQuery}</b>"</p>
                <button onClick={() => { setSearchQuery(""); setSelectedCategory("semua"); }} className="reset-btn">
                  Tampilkan Semua Alat
                </button>
              </div>
            ) : (
              <div className="products-horizontal-slider" ref={catalogScrollRef}>
                {filteredProducts.map((item) => (
                  <div key={item.id} className="shopee-card">
                    {/* Gambar / Visual Mockup Produk dengan Floating Trust Badges */}
                    <div className="shopee-card-media">
                      <div className="shopee-media-badges">
                        <div className="shopee-pill-rating" title={`Rating ${item.rating} dari 5`}>
                          <Star size={11} className="star-shopee" />
                          <span>{item.rating}</span>
                        </div>
                        <div className="shopee-pill-sold">
                          <span>{item.soldCount} Tersewa</span>
                        </div>
                      </div>

                      <div className="shopee-product-preview">
                        {renderProductIcon(item.category)}
                      </div>
                    </div>

                    {/* Body Kartu Produk (Lega, Bersih & Proporsional) */}
                    <div className="shopee-card-content">
                      {/* Judul Produk */}
                      <h3 className="shopee-title" title={item.name}>
                        {item.name}
                      </h3>

                      {/* Harga Sewa Utama (Clean & Bold) */}
                      <div className="shopee-price-container">
                        <div className="shopee-price-main">
                          <span className="shopee-currency">Rp</span>
                          <span className="shopee-amount">{(item.price).toLocaleString('id-ID')}</span>
                          <span className="shopee-per-day">/hari</span>
                        </div>
                      </div>

                      {/* Tombol Sewa Cepat */}
                      <button 
                        onClick={() => handleAddToCart(item)}
                        className="shopee-btn-rent"
                      >
                        + Sewa Sekarang
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {filteredProducts.length >= 6 && (
              <button 
                onClick={() => scrollCatalog('right')}
                className="catalog-floating-arrow arrow-right"
                aria-label="Geser ke kanan"
                title="Geser ke kanan"
              >
                <ChevronRight size={24} strokeWidth={2.5} />
              </button>
            )}
          </div>
      </div>
    </main>

      {/* 7. MODAL DRAWER KERANJANG PRODUK (POPUP CART MODAL) */}
      {isCartOpen && (
        <div className="cart-drawer-overlay" onClick={() => setIsCartOpen(false)}>
          <div className="cart-drawer" onClick={(e) => e.stopPropagation()}>
            {/* Header Keranjang */}
            <div className="cart-drawer-header">
              <div className="cart-header-title">
                <ShoppingCart size={20} className="text-primary" />
                <h3>Keranjang Sewa Alat ({totalCartCount})</h3>
              </div>
              <button 
                onClick={() => setIsCartOpen(false)}
                className="cart-close-btn"
                title="Tutup Keranjang"
              >
                <X size={20} />
              </button>
            </div>

            {/* Isi Keranjang */}
            <div className="cart-drawer-body">
              {cartItems.length === 0 ? (
                <div className="cart-empty-state">
                  <ShoppingBag size={48} className="cart-empty-icon" />
                  <h4>Keranjang Masih Kosong</h4>
                  <p>Yuk pilih peralatan camping impianmu dari katalog Sabana!</p>
                  <button onClick={() => setIsCartOpen(false)} className="cart-browse-btn">
                    Mulai Pilih Alat
                  </button>
                </div>
              ) : (
                <div className="cart-items-list">
                  {cartItems.map((item) => (
                    <div key={item.id} className="cart-item-card">
                      <div className="cart-item-icon">
                        <Tent size={26} />
                      </div>
                      <div className="cart-item-info">
                        <h4>{item.name}</h4>
                        <div className="cart-item-price">
                          {formatRupiah(item.price)} <span className="price-unit">/hari</span>
                        </div>
                        <div className="cart-item-controls">
                          <button onClick={() => updateCartQty(item.id, -1)} className="qty-btn">
                            <Minus size={14} />
                          </button>
                          <span className="qty-value">{item.qty}</span>
                          <button onClick={() => updateCartQty(item.id, 1)} className="qty-btn">
                            <Plus size={14} />
                          </button>
                          <button onClick={() => removeCartItem(item.id)} className="delete-btn" title="Hapus">
                            <Trash2 size={15} />
                          </button>
                        </div>
                      </div>
                      <div className="cart-item-subtotal">
                        {formatRupiah(item.price * item.qty)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer Keranjang & Checkout / Booking */}
            {cartItems.length > 0 && (
              <div className="cart-drawer-footer">
                <div className="cart-summary-row">
                  <span>Total Estimasi Sewa:</span>
                  <span className="cart-grand-total">{formatRupiah(totalCartPrice)}</span>
                </div>
                <p className="cart-promo-hint">
                  💡 Ingat: Sewa 3 hari otomatis hanya bayar 2 hari saat konfirmasi ke toko!
                </p>
                <div className="cart-checkout-actions">
                  <a
                    href={`https://wa.me/6281234567890?text=${encodeURIComponent(
                      `Halo Sabana Adventure, saya ingin sewa alat:\n` +
                      cartItems.map(i => `- ${i.name} (${i.qty} unit)`).join('\n') +
                      `\nTotal: ${formatRupiah(totalCartPrice)}/hari.`
                    )}`}
                    target="_blank"
                    rel="noreferrer"
                    className="cart-checkout-wa"
                  >
                    <Send size={16} /> Pesan via WhatsApp
                  </a>
                  <button
                    onClick={() => {
                      setIsCartOpen(false);
                      setIsChatOpen(true);
                    }}
                    className="cart-checkout-ai"
                  >
                    <MessageSquare size={16} /> Konsultasi ke AI
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 8. FOOTER RESMI SABANA ADVENTURE (CLEAN, ELEGAN & PROFESIONAL) */}
      <footer className="main-footer">
        <div className="footer-content-clean">
          {/* Kolom 1: Profil Toko & Jaminan Kualitas */}
          <div className="clean-footer-col">
            <div className="clean-footer-brand">
              <div className="clean-brand-icon">
                <Tent size={22} />
              </div>
              <div>
                <h3 className="clean-brand-name">Sabana Adventure</h3>
                <span className="clean-brand-tag">Persewaan Alat Camping &bull; Jombor, Sleman</span>
              </div>
            </div>
            <p className="clean-footer-text">
              Pusat rental perlengkapan camping dan pendakian gunung terlengkap di Sleman, D.I. Yogyakarta sejak 2020. Peralatan steril, bersih, dan siap badai.
            </p>
          </div>

          {/* Kolom 2: Lokasi Toko */}
          <div className="clean-footer-col">
            <h4 className="clean-col-title">Lokasi Toko</h4>
            <div className="simple-location-block">
              <div className="simple-info-row">
                <MapPin size={18} className="simple-info-icon" />
                <div className="simple-info-content">
                  <span className="simple-info-label">Alamat Toko</span>
                  <p className="simple-info-text">
                    Jl. Ringroad Utara No.163, Jombor Kidul, Sinduadi, Mlati, Sleman, DIY 55284
                  </p>
                </div>
              </div>

              <div className="simple-info-row">
                <Clock size={18} className="simple-info-icon" />
                <div className="simple-info-content">
                  <span className="simple-info-label">Jam Operasional</span>
                  <p className="simple-info-text">
                    Buka Setiap Hari: <b>08.00 – 21.00 WIB</b>
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Kolom 3: Media Sosial Resmi (Hanya Logo) */}
          <div className="clean-footer-col">
            <h4 className="clean-col-title">Media Sosial Resmi</h4>
            <p className="clean-footer-text">
              Ikuti akun media sosial resmi kami untuk melihat dokumentasi perlengkapan, video review, dan update promo:
            </p>
            <div className="social-icons-row">
              <a 
                href="https://www.tiktok.com/@sabanaadventure" 
                target="_blank" 
                rel="noreferrer" 
                className="social-circle-btn"
                title="TikTok @sabanaadventure"
                aria-label="TikTok"
              >
                <TikTokIcon size={20} />
              </a>

              <a 
                href="https://www.instagram.com/sabana_adventure" 
                target="_blank" 
                rel="noreferrer" 
                className="social-circle-btn"
                title="Instagram @sabana_adventure"
                aria-label="Instagram"
              >
                <InstagramIcon size={20} />
              </a>

              <a 
                href="https://wa.me/6281234567890" 
                target="_blank" 
                rel="noreferrer" 
                className="social-circle-btn"
                title="WhatsApp CS (0812-3456-7890)"
                aria-label="WhatsApp"
              >
                <WhatsAppIcon size={20} />
              </a>

              <a 
                href="https://www.facebook.com/sabanaadventurejogja" 
                target="_blank" 
                rel="noreferrer" 
                className="social-circle-btn"
                title="Facebook Sabana Adventure Jogja"
                aria-label="Facebook"
              >
                <FacebookIcon size={20} />
              </a>
            </div>
          </div>
        </div>

        {/* Footer Bottom Bar Bersih & Rapi */}
        <div className="clean-footer-bottom">
          <p>&copy; {new Date().getFullYear()} <b>Sabana Adventure Jombor</b>. Seluruh Hak Cipta Dilindungi.</p>
          <p className="clean-credits">
            Penyewaan Alat Outdoor &amp; Camping Terpercaya di Sleman, Yogyakarta
          </p>
        </div>
      </footer>

      {/* 9. TOMBOL TRIGGER WIDGET CHAT MELAYANG */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="floating-chat-trigger"
          title="Tanya Asisten Toko Sabana"
        >
          <MessageSquare size={26} />
        </button>
      )}

      {/* 10. KOMPONEN WIDGET CHAT AI */}
      <ChatWidget
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
}
