(() => {
    "use strict";

    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
    const toastRegion = $('[data-toast-region]');
    const modalState = { element: null, trigger: null };

    function showToast(message, isError = false) {
        if (!toastRegion || !message) return;
        const toast = document.createElement("div");
        toast.className = `toast${isError ? " toast-error" : ""}`;
        toast.setAttribute("role", isError ? "alert" : "status");
        toast.textContent = message;
        toastRegion.append(toast);
        window.setTimeout(() => toast.remove(), 4200);
    }

    function openModal(id, trigger = document.activeElement) {
        const modal = document.querySelector(`[data-modal="${id}"]`);
        if (!modal) return;
        closeModal();
        modalState.element = modal;
        modalState.trigger = trigger;
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";
        const focusTarget = $("input:not([type=hidden]), select, textarea, button", modal);
        if (focusTarget) window.setTimeout(() => focusTarget.focus(), 20);
    }

    function closeModal() {
        if (!modalState.element) return;
        const oldModal = modalState.element;
        oldModal.classList.remove("is-open");
        oldModal.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";
        const oldTrigger = modalState.trigger;
        modalState.element = null;
        modalState.trigger = null;
        if (oldTrigger && typeof oldTrigger.focus === "function") oldTrigger.focus();
    }

    $$("[data-open-modal]").forEach((button) => {
        button.addEventListener("click", () => {
            const form = $(`[data-modal="${button.dataset.openModal}"] form[data-ajax-form]`);
            if (form && button.dataset.openModal === "class-modal") resetEditForm(form, "schedule");
            if (form && button.dataset.openModal === "task-modal") resetEditForm(form, "task");
            openModal(button.dataset.openModal, button);
        });
    });

    $$("[data-close-modal]").forEach((button) => button.addEventListener("click", closeModal));
    $$("[data-modal]").forEach((modal) => {
        modal.addEventListener("mousedown", (event) => {
            if (event.target === modal) closeModal();
        });
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeModal();
            closeSidebar();
        }
        if (event.key === "/" && !isTextEntry(document.activeElement)) {
            const search = $("[data-task-search]");
            if (search) {
                event.preventDefault();
                search.focus();
            }
        }
        if (event.key === "Tab" && modalState.element) trapFocus(event, modalState.element);
    });

    function isTextEntry(element) {
        return element && (
            element.isContentEditable
            || ["INPUT", "TEXTAREA", "SELECT"].includes(element.tagName)
        );
    }

    function trapFocus(event, modal) {
        const focusable = $$(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
            modal
        ).filter((element) => element.offsetParent !== null);
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    }

    function resetEditForm(form, kind) {
        form.reset();
        form.action = kind === "schedule"
            ? form.dataset.createUrl || form.action.replace(/\/\d+\/update\/$/, "/create/")
            : form.dataset.createUrl || form.action.replace(/\/\d+\/update\/$/, "/create/");
        form.dataset.editing = "false";
        const title = $(`#${kind}-modal-title`);
        const submit = $('button[type="submit"]', form);
        if (title) title.textContent = kind === "schedule" ? "Add a class" : "Add a task";
        if (submit) submit.textContent = kind === "schedule" ? "Save class" : "Save task";
        $$("[data-error-for]", form).forEach((element) => {
            element.textContent = "";
            element.removeAttribute("data-invalid");
        });
    }

    function setField(form, name, value) {
        const field = form.elements.namedItem(name);
        if (field) field.value = value || "";
    }

    $$("[data-edit-schedule]").forEach((button) => {
        button.addEventListener("click", () => {
            const form = $('[data-modal="class-modal"] form');
            if (!form) return;
            resetEditForm(form, "schedule");
            form.action = button.dataset.updateUrl;
            form.dataset.editing = "true";
            Object.entries({
                subject_name: button.dataset.subjectName,
                subject_code: button.dataset.subjectCode,
                instructor: button.dataset.instructor,
                day: button.dataset.day,
                start_time: button.dataset.startTime,
                end_time: button.dataset.endTime,
                room: button.dataset.room
            }).forEach(([name, value]) => setField(form, name, value));
            $("#class-modal-title").textContent = "Edit class";
            $('button[type="submit"]', form).textContent = "Save changes";
            openModal("class-modal", button);
        });
    });

    $$("[data-edit-task]").forEach((button) => {
        button.addEventListener("click", () => {
            const form = $('[data-modal="task-modal"] form');
            if (!form) return;
            resetEditForm(form, "task");
            form.action = button.dataset.updateUrl;
            form.dataset.editing = "true";
            Object.entries({
                task_name: button.dataset.taskName,
                task_type: button.dataset.taskType,
                subject: button.dataset.subject,
                description: button.dataset.description,
                deadline: button.dataset.deadline,
                status: button.dataset.status,
                priority: button.dataset.priority
            }).forEach(([name, value]) => setField(form, name, value));
            $("#task-modal-title").textContent = "Edit task";
            $('button[type="submit"]', form).textContent = "Save changes";
            openModal("task-modal", button);
        });
    });

    $$("[data-confirm-delete]").forEach((button) => {
        button.addEventListener("click", () => {
            const form = $('[data-modal="delete-modal"] form');
            form.action = button.dataset.deleteUrl;
            $("[data-delete-name]").textContent = button.dataset.deleteName || "this item";
            openModal("delete-modal", button);
        });
    });

    function csrfToken(form) {
        const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (input) return input.value;
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function validateForm(form) {
        let valid = true;
        const kind = form.dataset.kind;
        if (kind === "schedule") {
            const start = form.elements.namedItem("start_time");
            const end = form.elements.namedItem("end_time");
            if (start && end && start.value && end.value && end.value <= start.value) {
                setError(form, "end_time", "End time must be later than start time.");
                valid = false;
            }
        }
        if (kind === "task") {
            const deadline = form.elements.namedItem("deadline");
            if (deadline && deadline.value && form.dataset.editing !== "true") {
                const chosen = new Date(deadline.value);
                if (chosen < new Date()) {
                    setError(form, "deadline", "Choose a deadline in the future.");
                    valid = false;
                }
            }
        }
        return valid;
    }

    function setError(form, fieldName, message) {
        const error = $(`[data-error-for="${fieldName}"]`, form);
        if (error) {
            error.textContent = message;
            error.dataset.invalid = "true";
        }
    }

    $$("[data-ajax-form]").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            if (!window.fetch || !window.FormData) return;
            event.preventDefault();
            $$("[data-error-for]", form).forEach((element) => {
                element.textContent = "";
                element.removeAttribute("data-invalid");
            });
            if (!validateForm(form)) {
                const error = $('[data-invalid="true"]', form);
                if (error) error.scrollIntoView({ block: "nearest" });
                return;
            }

            const submit = $('button[type="submit"]', form);
            if (submit) {
                submit.disabled = true;
                submit.classList.add("is-loading");
            }
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    headers: {
                        "X-CSRFToken": csrfToken(form),
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json"
                    },
                    credentials: "same-origin"
                });
                let result;
                try {
                    result = await response.json();
                } catch (error) {
                    throw new Error("The server returned an unexpected response.");
                }
                if (!response.ok || !result.ok) {
                    showToast(result.message || "Something went wrong. Please try again.", true);
                    displayServerErrors(form, result.errors);
                    return;
                }
                closeModal();
                showToast(result.message || "Saved.");
                window.setTimeout(() => window.location.reload(), 550);
            } catch (error) {
                showToast(error.message || "Couldn't save your changes. Check your connection and try again.", true);
            } finally {
                if (submit) {
                    submit.disabled = false;
                    submit.classList.remove("is-loading");
                }
            }
        });
    });

    function displayServerErrors(form, errors) {
        if (!errors || typeof errors !== "object") return;
        Object.entries(errors).forEach(([fieldName, messages]) => {
            const message = Array.isArray(messages)
                ? messages.map((item) => typeof item === "string" ? item : item.message).join(" ")
                : String(messages);
            setError(form, fieldName, message);
        });
    }

    $$("[data-task-complete]").forEach((button) => {
        button.addEventListener("click", async () => {
            const complete = button.getAttribute("aria-pressed") !== "true";
            const form = $('[data-modal="task-modal"] form');
            const data = new FormData(form);
            data.set("task_name", button.dataset.taskName);
            data.set("task_type", button.dataset.taskType);
            data.set("subject", button.dataset.subject || "");
            data.set("description", button.dataset.description || "");
            data.set("deadline", button.dataset.deadline);
            data.set("status", complete ? "Completed" : "Pending");
            data.set("priority", button.dataset.priority);
            button.disabled = true;
            try {
                const response = await fetch(button.dataset.updateUrl, {
                    method: "POST",
                    body: data,
                    headers: {
                        "X-CSRFToken": csrfToken(form),
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json"
                    },
                    credentials: "same-origin"
                });
                const result = await response.json();
                if (!response.ok || !result.ok) throw new Error(result.message || "Couldn't update this task.");
                showToast(complete ? "Nice work — task completed." : "Task moved back to pending.");
                window.setTimeout(() => window.location.reload(), 500);
            } catch (error) {
                showToast(error.message || "Couldn't update this task. Check your connection and try again.", true);
                button.disabled = false;
            }
        });
    });

    const filterButtons = $$("[data-task-filter]");
    const taskRows = $$("[data-task-row]");
    let activeFilter = "all";
    let searchTerm = "";

    function applyTaskFilters() {
        let visible = 0;
        taskRows.forEach((row) => {
            const statusMatches = activeFilter === "all" || row.dataset.status === activeFilter;
            const textMatches = (row.dataset.search || "").includes(searchTerm);
            const show = statusMatches && textMatches;
            row.hidden = !show;
            if (show) visible += 1;
        });
        const empty = $("[data-search-empty]");
        if (empty) empty.hidden = visible !== 0 || taskRows.length === 0;
    }

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeFilter = button.dataset.taskFilter;
            filterButtons.forEach((item) => {
                const selected = item === button;
                item.classList.toggle("is-active", selected);
                item.setAttribute("aria-pressed", String(selected));
            });
            applyTaskFilters();
        });
    });
    $$("[data-task-search]").forEach((input) => {
        input.addEventListener("input", () => {
            searchTerm = input.value.trim().toLocaleLowerCase();
            $$("[data-task-search]").forEach((other) => {
                if (other !== input) other.value = input.value;
            });
            applyTaskFilters();
        });
    });

    $$("[data-schedule-view]").forEach((button) => {
        button.addEventListener("click", () => {
            const gridView = button.dataset.scheduleView === "grid";
            const grid = $("[data-schedule-grid]");
            const list = $("[data-schedule-list]");
            if (!grid || !list) return;
            grid.hidden = !gridView;
            list.hidden = gridView;
            $$("[data-schedule-view]").forEach((item) => {
                const selected = item === button;
                item.classList.toggle("is-selected", selected);
                item.setAttribute("aria-pressed", String(selected));
            });
        });
    });

    function updateCountdowns() {
        $$("[data-due-item]").forEach((item) => {
            const date = new Date(item.dataset.deadline);
            const output = $("[data-countdown]", item);
            if (!output || Number.isNaN(date.getTime())) return;
            const diff = date.getTime() - Date.now();
            if (diff < 0) {
                output.textContent = "Overdue";
                output.classList.add("is-urgent");
            } else if (diff < 60 * 60 * 1000) {
                output.textContent = "Due soon";
                output.classList.add("is-urgent");
            } else if (diff < 24 * 60 * 60 * 1000) {
                const hours = Math.max(1, Math.ceil(diff / (60 * 60 * 1000)));
                output.textContent = `${hours}h left`;
                if (hours <= 6) output.classList.add("is-urgent");
            } else {
                const days = Math.ceil(diff / (24 * 60 * 60 * 1000));
                output.textContent = `${days} day${days === 1 ? "" : "s"}`;
            }
        });
    }
    updateCountdowns();

    const themeKey = "studyday-theme";
    function setTheme(theme) {
        document.documentElement.dataset.theme = theme;
        try {
            window.localStorage.setItem(themeKey, theme);
        } catch (error) {
            // Storage may be unavailable in private browsing; the current page still changes.
        }
    }
    try {
        const storedTheme = window.localStorage.getItem(themeKey);
        if (storedTheme === "dark" || storedTheme === "light") {
            document.documentElement.dataset.theme = storedTheme;
        }
    } catch (error) {
        // Use the default light theme when storage is unavailable.
    }
    $$("[data-theme-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
            setTheme(nextTheme);
        });
    });

    $$("[data-password-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.passwordToggle);
            if (!input) return;
            const show = input.type === "password";
            input.type = show ? "text" : "password";
            button.textContent = show ? "Hide" : "Show";
            button.setAttribute("aria-label", `${show ? "Hide" : "Show"} password`);
        });
    });

    const sidebar = $("#sidebar");
    const sidebarScrim = $("[data-sidebar-scrim]");
    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove("is-open");
        if (sidebarScrim) sidebarScrim.classList.remove("is-visible");
    }
    const sidebarToggle = $("[data-sidebar-toggle]");
    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            if (!sidebar) return;
            sidebar.classList.toggle("is-open");
            if (sidebarScrim) sidebarScrim.classList.toggle("is-visible");
        });
    }
    if (sidebarScrim) sidebarScrim.addEventListener("click", closeSidebar);

    $$("[data-nav-target]").forEach((link) => {
        link.addEventListener("click", () => {
            $$("[data-nav-target]").forEach((item) => item.classList.toggle("is-active", item === link));
            closeSidebar();
        });
    });

    $$("[data-sidebar-scrim]").forEach((element) => element.addEventListener("click", closeSidebar));
    $$(".flash-dismiss").forEach((button) => button.addEventListener("click", () => {
        const message = button.closest(".flash-message");
        if (message) message.remove();
    }));
    $$(".flash-message").forEach((message) => {
        const text = message.querySelector("span");
        if (text) showToast(text.textContent, message.classList.contains("flash-error"));
    });

    initCalendar();

    function initCalendar() {
        const container = $("[data-calendar-grid]");
        const label = $("[data-calendar-label]");
        const source = $("#calendar-data");
        if (!container || !label || !source) return;
        let data;
        try {
            data = JSON.parse(source.textContent);
        } catch (error) {
            showToast("The calendar could not load its event data.", true);
            return;
        }
        const events = Array.isArray(data.tasks) ? data.tasks : [];
        const today = new Date();
        let year = today.getFullYear();
        let month = today.getMonth();

        function getEventsForDay(date) {
            return events.filter((event) => {
                if (event.type === "task") {
                    const deadline = new Date(event.deadline);
                    return deadline.getFullYear() === date.getFullYear()
                        && deadline.getMonth() === date.getMonth()
                        && deadline.getDate() === date.getDate();
                }
                return date.getDay() === weekdayNumber(event.day);
            });
        }

        function weekdayNumber(day) {
            return ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].indexOf(day);
        }

        function render() {
            container.replaceChildren();
            label.textContent = new Intl.DateTimeFormat(undefined, {
                month: "long",
                year: "numeric"
            }).format(new Date(year, month, 1));
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].forEach((day) => {
                const weekday = document.createElement("span");
                weekday.className = "calendar-weekday";
                weekday.textContent = day;
                container.append(weekday);
            });

            const first = new Date(year, month, 1);
            const startOffset = (first.getDay() + 6) % 7;
            const start = new Date(year, month, 1 - startOffset);
            for (let index = 0; index < 42; index += 1) {
                const day = new Date(start.getFullYear(), start.getMonth(), start.getDate() + index);
                const dayEvents = getEventsForDay(day);
                const cell = document.createElement("button");
                cell.type = "button";
                cell.className = "calendar-cell";
                if (day.getMonth() !== month) cell.classList.add("is-outside");
                if (sameDay(day, today)) cell.classList.add("is-today");
                cell.setAttribute("aria-label", `${day.toLocaleDateString()}${dayEvents.length ? `, ${dayEvents.length} events` : ""}`);
                const number = document.createElement("span");
                number.textContent = String(day.getDate());
                cell.append(number);
                if (dayEvents.length) {
                    const dots = document.createElement("span");
                    dots.className = "calendar-dots";
                    const hasClass = dayEvents.some((event) => event.type === "class");
                    const hasTask = dayEvents.some((event) => event.type === "task");
                    if (hasClass) {
                        const dot = document.createElement("i");
                        dot.className = "calendar-dot calendar-dot-class";
                        dots.append(dot);
                    }
                    if (hasTask) {
                        const dot = document.createElement("i");
                        dot.className = "calendar-dot calendar-dot-task";
                        dots.append(dot);
                    }
                    cell.append(dots);
                }
                cell.addEventListener("click", () => showCalendarDay(day, dayEvents, cell));
                container.append(cell);
            }
        }

        function sameDay(first, second) {
            return first.getFullYear() === second.getFullYear()
                && first.getMonth() === second.getMonth()
                && first.getDate() === second.getDate();
        }

        function showCalendarDay(day, dayEvents, trigger) {
            const modal = $('[data-modal="calendar-day-modal"]');
            const title = $("#calendar-day-title");
            const content = $("[data-calendar-day-content]");
            if (!modal || !title || !content) return;
            title.textContent = new Intl.DateTimeFormat(undefined, {
                weekday: "long",
                month: "long",
                day: "numeric"
            }).format(day);
            content.replaceChildren();
            if (!dayEvents.length) {
                const empty = document.createElement("p");
                empty.className = "confirm-copy";
                empty.textContent = "Nothing planned for this day. Leave yourself some breathing room.";
                content.append(empty);
            }
            dayEvents.forEach((event) => {
                const entry = document.createElement("div");
                entry.className = "calendar-day-entry";
                const mark = document.createElement("i");
                mark.className = `calendar-entry-mark${event.type === "class" ? " is-class" : ""}`;
                const copy = document.createElement("div");
                const name = document.createElement("strong");
                name.textContent = event.name;
                const detail = document.createElement("span");
                detail.textContent = event.type === "class"
                    ? `${event.start}–${event.end} · ${event.day}`
                    : `${event.type} · ${new Date(event.deadline).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
                copy.append(name, detail);
                entry.append(mark, copy);
                content.append(entry);
            });
            openModal("calendar-day-modal", trigger);
        }

        const previous = $("[data-calendar-prev]");
        const next = $("[data-calendar-next]");
        if (previous) previous.addEventListener("click", () => {
            month -= 1;
            if (month < 0) {
                month = 11;
                year -= 1;
            }
            render();
        });
        if (next) next.addEventListener("click", () => {
            month += 1;
            if (month > 11) {
                month = 0;
                year += 1;
            }
            render();
        });
        render();
    }
})();
