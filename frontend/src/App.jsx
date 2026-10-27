import React, { useState, useEffect, useRef } from 'react';
import { 
  Tent, Compass, Search, ShoppingBag, Heart, User, Phone, 
  MessageSquare, ChevronLeft, ChevronRight, Star, Flame, 
  ShieldCheck, Clock, CheckCircle2, Tag, Filter, Sparkles,
  ArrowRight, Shield, Zap, ThumbsUp, PackageCheck, X, Trash2,
  Plus, Minus, ShoppingCart, Send
} from 'lucide-react';
import ChatWidget from './components/ChatWidget';
import './App.css';

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
      {/* 1. TOP ANNOUNCEMENT BAR */}
      <div className="top-bar">
        <div className="top-bar-inner">
          <div className="top-bar-info">
            <span className="top-tag">SABANA PROMO</span>
            <span>Aturan Sewa: Sewa 3 hari dihitung tarif 2 hari &bull; Ambil H-1 Sore Bebas Biaya Tambahan!</span>
          </div>
          <div className="top-bar-links">
            <a href="https://wa.me/6281234567890" target="_blank" rel="noreferrer" className="top-link">
              <Phone size={13} /> CS WhatsApp: 0812-3456-7890
            </a>
            <span className="top-sep">|</span>
            <span className="top-loc">Lokasi: Jombor, Sleman</span>
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

          {/* User & Cart Actions (Hanya Keranjang Produk) */}
          <div className="header-actions">
            <div 
              className="cart-action-btn" 
              onClick={() => setIsCartOpen(true)} 
              title="Buka Keranjang Sewa"
            >
              <div className="cart-icon-wrapper">
                <ShoppingCart size={22} />
                {totalCartCount > 0 && <span className="cart-badge">{totalCartCount}</span>}
              </div>
              <div className="cart-text-group">
                <span className="btn-label-cart">Keranjang</span>
                <span className="cart-total-preview">{formatRupiah(totalCartPrice)}</span>
              </div>
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
                Geser ke kanan untuk melihat seluruh alat &bull; Tersedia <b>{filteredProducts.length}</b> peralatan
              </p>
            </div>
          </div>

          {/* Wrapper Slider Horizontal dengan Tombol Melayang Samping */}
          <div className="catalog-slider-wrapper">
            <button 
              onClick={() => scrollCatalog('left')}
              className="catalog-floating-arrow arrow-left"
              aria-label="Geser ke kiri"
              title="Geser ke kiri"
            >
              <ChevronLeft size={22} />
            </button>

            {filteredProducts.length === 0 ? (
              <div className="empty-catalog">
                <p>Tidak ditemukan alat dengan kata kunci "<b>{searchQuery}</b>"</p>
                <button onClick={() => { setSearchQuery(""); setSelectedCategory("semua"); }} className="reset-btn">
                  Tampilkan Semua Alat
                </button>
              </div>
            ) : (
              <>
                <div className="products-horizontal-slider" ref={catalogScrollRef}>
                {filteredProducts.map((item) => (
                  <div key={item.id} className="shopee-card">
                    {/* Gambar / Visual Mockup Produk */}
                    <div className="shopee-card-media">
                      <div className="shopee-top-badges">
                        <span className="shopee-badge-mall">{item.badge}</span>
                        <span className="shopee-badge-loc">{item.location}</span>
                      </div>

                      <div className="shopee-product-preview">
                        <Tent size={52} className="shopee-preview-icon" />
                        <span className="shopee-cat-tag">{item.category.toUpperCase()}</span>
                      </div>
                    </div>

                  {/* Body Kartu Produk */}
                  <div className="shopee-card-content">
                    {/* Judul Produk */}
                    <h3 className="shopee-title" title={item.name}>
                      {item.name}
                    </h3>

                    {/* Tag Fitur Singkat */}
                    <div className="shopee-tags-row">
                      {item.tags.slice(0, 2).map((tag, idx) => (
                        <span key={idx} className="shopee-mini-tag">{tag}</span>
                      ))}
                    </div>

                    {/* Harga Coret & Harga Sewa */}
                    <div className="shopee-price-container">
                      <div className="shopee-strike-row">
                        <span className="shopee-original-price">{formatRupiah(item.originalPrice)}</span>
                        <span className="shopee-disc-badge">HEMAT</span>
                      </div>
                      <div className="shopee-price-main">
                        <span className="shopee-currency">Rp</span>
                        <span className="shopee-amount">{(item.price).toLocaleString('id-ID')}</span>
                        <span className="shopee-per-day">/hari</span>
                      </div>
                    </div>

                    {/* Rating Bintang & Terjual / Tersewa */}
                    <div className="shopee-metrics-row">
                      <div className="shopee-rating">
                        <Star size={12} className="star-shopee" />
                        <span>{item.rating}</span>
                      </div>
                      <span className="shopee-sold">{item.soldCount} Tersewa</span>
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

              <button 
                onClick={() => scrollCatalog('right')}
                className="catalog-floating-arrow arrow-right"
                aria-label="Geser ke kanan"
                title="Geser ke kanan"
              >
                <ChevronRight size={22} />
              </button>
            </>
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

      {/* 8. FOOTER E-COMMERCE */}
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
