document.addEventListener("DOMContentLoaded", () => {
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
			} else {
				entry.target.classList.remove("visible");
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
		bookingForm.addEventListener("submit", (e) => {
			e.preventDefault();

			const formData = new FormData(bookingForm);
			const name = formData.get("name");

			formMessage.textContent = `Thank you, ${name}! Your booking request has been received. We will contact you shortly to confirm.`;
			formMessage.className = "form-message success";

			bookingForm.reset();

			setTimeout(() => {
				formMessage.style.display = "none";
			}, 5000);
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
			}
		};

		setTimeout(typeWriter, 800);
	}

	const canvas = document.getElementById("cursor-canvas");
	if (canvas) {
		const ctx = canvas.getContext("2d");
		let width = (canvas.width = window.innerWidth);
		let height = (canvas.height = window.innerHeight);

		let mouse = { x: width / 2, y: height / 2 };
		let dot = { x: width / 2, y: height / 2 };
		let circle = { x: width / 2, y: height / 2 };

		let isHovering = false;

		window.addEventListener("resize", () => {
			width = canvas.width = window.innerWidth;
			height = canvas.height = window.innerHeight;
		});

		window.addEventListener("mousemove", (e) => {
			mouse.x = e.clientX;
			mouse.y = e.clientY;
		});

		const interactables = "a, button, .instagram-item, .gallery-item";
		document.addEventListener("mouseover", (e) => {
			if (e.target.closest(interactables)) isHovering = true;
		});
		document.addEventListener("mouseout", (e) => {
			if (e.target.closest(interactables)) isHovering = false;
		});

		const animateCursor = () => {
			ctx.clearRect(0, 0, width, height);

			dot.x += (mouse.x - dot.x) * 0.2;
			dot.y += (mouse.y - dot.y) * 0.2;

			circle.x += (mouse.x - circle.x) * 0.1;
			circle.y += (mouse.y - circle.y) * 0.1;

			const color = "#36454F";
			const targetCircleSize = isHovering ? 30 : 20;
			const currentCircleSize = circle.size || 20;
			circle.size =
				currentCircleSize + (targetCircleSize - currentCircleSize) * 0.1;

			ctx.strokeStyle = color;
			ctx.lineWidth = 1;
			ctx.beginPath();
			ctx.arc(circle.x, circle.y, circle.size, 0, Math.PI * 2);
			ctx.stroke();

			ctx.fillStyle = color;
			ctx.beginPath();
			ctx.arc(dot.x, dot.y, isHovering ? 4 : 2, 0, Math.PI * 2);
			ctx.fill();

			requestAnimationFrame(animateCursor);
		};

		animateCursor();
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
});
