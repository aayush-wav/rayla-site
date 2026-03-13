document.addEventListener("DOMContentLoaded", () => {
	// Root level theme check to prevent flickering
	const currentTheme = localStorage.getItem("theme");
	if (currentTheme === "dark") {
		document.body.classList.add("dark-mode");
	}

	const navbar = document.querySelector(".navbar");
	window.addEventListener("scroll", () => {
		if (window.scrollY > 50) {
			navbar.classList.add("scrolled");
		} else {
			navbar.classList.remove("scrolled");
		}
	});

	const hamburger = document.querySelector(".hamburger");
	const navLinks = document.querySelector(".nav-links");

	hamburger.addEventListener("click", () => {
		navLinks.classList.toggle("active");

		const spans = hamburger.querySelectorAll("span");
		if (navLinks.classList.contains("active")) {
			spans[0].style.transform = "rotate(45deg) translate(5px, 5px)";
			spans[1].style.opacity = "0";
			spans[2].style.transform = "rotate(-45deg) translate(5px, -5px)";
		} else {
			spans[0].style.transform = "none";
			spans[1].style.opacity = "1";
			spans[2].style.transform = "none";
		}
	});

	document.querySelectorAll(".nav-links a").forEach((link) => {
		link.addEventListener("click", () => {
			if (navLinks.classList.contains("active")) {
				navLinks.classList.remove("active");
				const spans = hamburger.querySelectorAll("span");
				spans[0].style.transform = "none";
				spans[1].style.opacity = "1";
				spans[2].style.transform = "none";
			}
		});
	});

	const fadeElements = document.querySelectorAll(".fade-in-up");

	const observerOptions = {
		root: null,
		rootMargin: "0px",
		threshold: 0.15,
	};

	const observer = new IntersectionObserver((entries) => {
		entries.forEach((entry) => {
			if (entry.isIntersecting) {
				entry.target.classList.add("visible");
				observer.unobserve(entry.target);
			}
		});
	}, observerOptions);

	fadeElements.forEach((el) => observer.observe(el));

	const backToTop = document.getElementById("back-to-top");
	if (backToTop) {
		window.addEventListener("scroll", () => {
			if (window.scrollY > 300) {
				backToTop.classList.add("show");
			} else {
				backToTop.classList.remove("show");
			}
		});
	}

	const bookingForm = document.getElementById("booking-form");
	const formMessage = document.getElementById("form-message");

	if (bookingForm) {
		bookingForm.addEventListener("submit", async (e) => {
			e.preventDefault();

			const submitBtn = bookingForm.querySelector('button[type="submit"]');
			const originalBtnText = submitBtn.textContent;
			submitBtn.disabled = true;
			submitBtn.textContent = "Processing...";

			const formData = new FormData(bookingForm);
			const data = {
				name: formData.get("name"),
				phone: formData.get("phone"),
				service: formData.get("service"),
				sub_service: formData.get("sub-service") || "N/A",
				date: formData.get("date"),
				time: formData.get("time"),
			};

			try {
				const response = await fetch("/api/booking", {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: JSON.stringify(data),
				});

				const result = await response.json();

				if (response.ok) {
					window.location.href = "/confirmation.html";
				} else {
					throw new Error(result.error || "Something went wrong");
				}
			} catch (error) {
				formMessage.textContent = `Error: ${error.message}. Please try again later.`;
				formMessage.className = "form-message error";
				formMessage.style.display = "block";
				formMessage.style.backgroundColor = "#f8d7da";
				formMessage.style.color = "#721c24";
				formMessage.style.border = "1px solid #f5c6cb";
			} finally {
				submitBtn.disabled = false;
				submitBtn.textContent = originalBtnText;

				setTimeout(() => {
					formMessage.style.display = "none";
				}, 6000);
			}
		});
	}

	const typeWriterElement = document.getElementById("typewriter-text");
	if (typeWriterElement) {
		const textToType = "Chic Nails,\nEffortless Style.";
		let i = 0;
		const typeWriter = () => {
			if (i < textToType.length) {
				if (textToType.charAt(i) === "\n") {
					typeWriterElement.innerHTML += "<br>";
				} else {
					typeWriterElement.innerHTML += textToType.charAt(i);
				}
				i++;
				setTimeout(typeWriter, 120);
			} else {
				startCursor();
			}
		};

		setTimeout(typeWriter, 800);
	}

	let cursorStarted = false;
	let existenceFactor = 0;
	const startCursor = () => {
		cursorStarted = true;
	};

	const serviceSelect = document.getElementById("service");
	const subServiceGroup = document.getElementById("sub-service-group");
	const subServiceSelect = document.getElementById("sub-service");
	const subServiceLabel = document.getElementById("sub-service-label");

	const subOptions = {
		"nail-extensions": [
			{ value: "gel", text: "Gel (NPR 1500)" },
			{ value: "gelx", text: "GelX (NPR 1400)" },
			{ value: "acrylic", text: "Acrylic (NPR 1800)" },
			{ value: "polygel", text: "Polygel (NPR 1500)" },
			{ value: "overlay", text: "Overlay (NPR 1000)" },
			{ value: "choose-on-visit", text: "Choose on Visit" },
		],
		"lash-extensions": [
			{ value: "classic", text: "Classic Lashes (NPR 1500)" },
			{ value: "cateye", text: "Cateye Lashes (NPR 1800)" },
			{ value: "wispy", text: "Wispy Lashes (NPR 2000)" },
			{ value: "lift", text: "Lashes Lift (NPR 1500)" },
			{ value: "choose-on-visit", text: "Choose on Visit" },
		],
		removal: [
			{ value: "nail-removal", text: "Nail Extension Removal (NPR 500)" },
			{ value: "lash-removal", text: "Lash Extension Removal (NPR 700)" },
			{ value: "choose-on-visit", text: "Choose on Visit" },
		],
		courses: [
			{ value: "nail-basic", text: "Nail Basic (NPR 10,000)" },
			{ value: "nail-pro", text: "Nail Professional (NPR 33,000)" },
			{ value: "lash-basic", text: "Lash Basic (NPR 5,000)" },
			{ value: "lash-pro", text: "Lash Professional (NPR 16,000)" },
			{ value: "choose-on-visit", text: "Talk to Expert on Visit" },
		],
	};

	if (serviceSelect) {
		serviceSelect.addEventListener("change", () => {
			const selected = serviceSelect.value;
			if (subOptions[selected]) {
				subServiceSelect.innerHTML = "";

				const placeholder = document.createElement("option");
				placeholder.value = "";
				placeholder.disabled = true;
				placeholder.selected = true;
				placeholder.textContent = "Select specific type...";
				subServiceSelect.appendChild(placeholder);

				subOptions[selected].forEach((opt) => {
					const o = document.createElement("option");
					o.value = opt.value;
					o.textContent = opt.text;
					subServiceSelect.appendChild(o);
				});

				subServiceGroup.style.display = "block";
				subServiceSelect.required = true;
			} else {
				subServiceGroup.style.display = "none";
				subServiceSelect.required = false;
			}
		});
	}

	const dateInput = document.getElementById("date");
	const timeSlotGroup = document.getElementById("time-slot-group");
	const timeSelect = document.getElementById("time");

	if (dateInput) {
		dateInput.addEventListener("change", async () => {
			const selectedDate = dateInput.value;
			if (!selectedDate) return;

			timeSelect.innerHTML =
				'<option value="" disabled selected>Loading slots...</option>';
			timeSlotGroup.style.display = "block";
			timeSelect.required = true;

			try {
				const res = await fetch(`/api/availability?date=${selectedDate}`);
				const data = await res.json();

				timeSelect.innerHTML = "";

				if (data.blocked) {
					const opt = document.createElement("option");
					opt.value = "";
					opt.disabled = true;
					opt.selected = true;
					opt.textContent = "❌ This day is fully booked";
					timeSelect.appendChild(opt);
				} else if (data.available_slots.length === 0) {
					const opt = document.createElement("option");
					opt.value = "";
					opt.disabled = true;
					opt.selected = true;
					opt.textContent = "❌ No slots available for this day";
					timeSelect.appendChild(opt);
				} else {
					const placeholder = document.createElement("option");
					placeholder.value = "";
					placeholder.disabled = true;
					placeholder.selected = true;
					placeholder.textContent = "Select a time...";
					timeSelect.appendChild(placeholder);

					data.available_slots.forEach((slot) => {
						const opt = document.createElement("option");
						opt.value = slot;
						opt.textContent = slot;
						timeSelect.appendChild(opt);
					});
				}
			} catch (err) {
				console.error("Availability Fetch Error:", err);
				timeSelect.innerHTML =
					'<option value="" disabled selected>Could not load slots</option>';
			}
		});
	}

	const initInstagram = async () => {
		const grid = document.getElementById("instagram-api-grid");

		const accessToken = "YOUR_ACCESS_TOKEN_HERE";
		const count = 6;

		if (!grid || accessToken === "YOUR_ACCESS_TOKEN_HERE") return;

		try {
			const response = await fetch(
				`https://graph.instagram.com/me/media?fields=id,caption,media_type,media_url,permalink,thumbnail_url,timestamp&access_token=${accessToken}`,
			);
			const result = await response.json();

			if (result.data) {
				grid.innerHTML = "";

				const posts = result.data.slice(0, count);
				posts.forEach((post) => {
					const mediaUrl =
						post.media_type === "VIDEO" ? post.thumbnail_url : post.media_url;

					const item = document.createElement("a");
					item.href = post.permalink;
					item.target = "_blank";
					item.className = "instagram-item fade-in-up";

					item.innerHTML = `
                        <img src="${mediaUrl}" alt="${post.caption || "Instagram post"}" loading="lazy">
                        <div class="instagram-overlay">
                            <svg viewBox="0 0 24 24" width="24" height="24" fill="white">
                                <path d="M12 12.37A4 4 0 1 1 12 4a4 4 0 0 1 0 8.37zm0-6.37a2.37 2.37 0 1 0 0 4.74 2.37 2.37 0 0 0 0-4.74zM22 12c0 5.52-4.48 10-10 10S2 17.52 2 12 6.48 2 12 2s10 4.48 10 10zm-2 0c0-4.42-3.58-8-8-8s-8 3.58-8 8 3.58 8 8 8 8-3.58 8-8z"/>
                            </svg>
                        </div>
                    `;
					grid.appendChild(item);
				});

				const newItems = grid.querySelectorAll(".fade-in-up");
				newItems.forEach((el) => observer.observe(el));
			}
		} catch (error) {
			console.error("Error fetching Instagram feed:", error);
			grid.innerHTML =
				'<p style="grid-column: 1/-1;">Check back soon for latest updates.</p>';
		}
	};

	initInstagram();

	// --- Monochrome Cursor Overlay & Grid Warp ---
	const initMonochromeCursor = () => {
		const canvas = document.getElementById("cursor-canvas");
		const hero = document.querySelector(".hero");
		if (!canvas || !hero) return;

		const ctx = canvas.getContext("2d");
		let width, height;
		
		const resize = () => {
			width = window.innerWidth;
			height = window.innerHeight;
			canvas.width = width;
			canvas.height = height;
		};
		window.addEventListener("resize", resize);
		resize();

		const pos = { x: width / 2, y: height / 2 };
		let velocity = 0;
		let warpStrength = 0;
		let globalAlpha = 0; // Transition alpha
		const lerp = (a, b, n) => (1 - n) * a + n * b;

		// Monochrome dots: darker on light mode, lighter on dark mode
		const getColor = (alpha) => {
			const isDark = document.body.classList.contains("dark-mode");
			const baseColor = isDark ? "255, 255, 255" : "26, 26, 26";
			return `rgba(${baseColor}, ${alpha * globalAlpha})`;
		};

		// 1. Grid Warp Configuration
		const gridSpacing = 36;
		const influenceRadius = 140; // Increased influence radius
		const mouse = { x: width / 2, y: height / 2, lastX: width / 2, lastY: height / 2, active: false };

		const updatePosition = (e) => {
			mouse.x = e.clientX;
			mouse.y = e.clientY;
			
			const rect = hero.getBoundingClientRect();
			mouse.active = (
				mouse.x >= rect.left && 
				mouse.x <= rect.right && 
				mouse.y >= rect.top && 
				mouse.y <= rect.bottom
			);
		};

		window.addEventListener("mousemove", updatePosition);
		window.addEventListener("scroll", () => {
			updatePosition({ clientX: mouse.x, clientY: mouse.y });
		});

		window.addEventListener("mouseleave", () => {
			velocity = 0;
			warpStrength = 0;
			mouse.active = false;
		});

		const animate = () => {
			// Calculate velocity
			const dx = mouse.x - mouse.lastX;
			const dy = mouse.y - mouse.lastY;
			const instantVel = Math.sqrt(dx * dx + dy * dy);
			velocity = lerp(velocity, instantVel, 0.1);
			warpStrength = lerp(warpStrength, Math.min(velocity * 0.2, 3.5), 0.1); // Increased multiplier and cap
			
			// Handle smooth transition when entering/leaving hero
			globalAlpha = lerp(globalAlpha, mouse.active ? 1 : 0, 0.1);

			mouse.lastX = mouse.x;
			mouse.lastY = mouse.y;

			ctx.clearRect(0, 0, width, height);

			const heroRect = hero.getBoundingClientRect();
			const isInView = heroRect.bottom > 0 && heroRect.top < height;

			if (!isInView && globalAlpha < 0.01) {
				requestAnimationFrame(animate);
				return;
			}

			// --- Layer 1: Grid Warp (Background dots) ---
			// We draw these dots even if not hovering, as long as hero is in view
			const startCol = 0;
			const endCol = Math.ceil(width / gridSpacing);
			const startRow = Math.max(0, Math.floor(heroRect.top / gridSpacing));
			const endRow = Math.min(Math.ceil(height / gridSpacing), Math.ceil(heroRect.bottom / gridSpacing));
			
			for (let i = startCol; i <= endCol; i++) {
				for (let j = startRow; j <= endRow; j++) {
					let x = i * gridSpacing;
					let y = j * gridSpacing;

					const distDx = x - mouse.x;
					const distDy = y - mouse.y;
					const dist = Math.sqrt(distDx * distDx + distDy * distDy);

					if (dist < influenceRadius && globalAlpha > 0.01) {
						// Radial bulge distortion away from cursor - only when hovering
						const force = (1 - dist / influenceRadius) ** 2;
						const angle = Math.atan2(distDy, distDx);
						const shift = force * warpStrength * 24 * globalAlpha; // Increased shift multiplier
						x += Math.cos(angle) * shift;
						y += Math.sin(angle) * shift;
					}

					ctx.beginPath();
					ctx.arc(x, y, 1.2, 0, Math.PI * 2); 
					// Base alpha for dots is 0.2, increasing slightly on hover
					ctx.fillStyle = `rgba(30, 30, 30, ${0.2 + (0.3 * globalAlpha)})`;
					ctx.fill();
				}
			}

			requestAnimationFrame(animate);
		};

		animate();
	};

	const themeToggle = document.getElementById("theme-toggle");
	if (themeToggle) {
		themeToggle.addEventListener("click", () => {
			document.body.classList.toggle("dark-mode");
			const theme = document.body.classList.contains("dark-mode") ? "dark" : "light";
			localStorage.setItem("theme", theme);
		});
	}

	initMonochromeCursor();
});
