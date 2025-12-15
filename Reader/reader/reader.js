/**
 * Reader.js - Core utilities for the reading system
 * Handles localStorage operations for reading progress
 */

// LocalStorage keys format:
// reading_progress::{book_id}::{chapter_id} -> { scrollY, timestamp }
// last_opened_chapter::{book_id} -> { chapter_id, timestamp }

/**
 * Save scroll position for a chapter
 */
function saveScrollPosition(bookId, chapterId, scrollY) {
    const key = `reading_progress::${bookId}::${chapterId}`;
    const data = {
        scrollY: scrollY,
        timestamp: Date.now()
    };
    localStorage.setItem(key, JSON.stringify(data));
}

/**
 * Get scroll position for a chapter
 */
function getScrollPosition(bookId, chapterId) {
    const key = `reading_progress::${bookId}::${chapterId}`;
    const data = localStorage.getItem(key);

    if (data) {
        try {
            return JSON.parse(data);
        } catch (e) {
            return null;
        }
    }

    return null;
}

/**
 * Restore scroll position for a chapter
 */
function restoreScrollPosition(bookId, chapterId) {
    const progress = getScrollPosition(bookId, chapterId);

    if (progress && progress.scrollY) {
        // Wait for content to render
        setTimeout(() => {
            window.scrollTo({
                top: progress.scrollY,
                behavior: 'smooth'
            });
        }, 100);
    }
}

/**
 * Save the last opened chapter for a book
 */
function saveLastOpenedChapter(bookId, chapterId) {
    const key = `last_opened_chapter::${bookId}`;
    const data = {
        chapter_id: chapterId,
        timestamp: Date.now()
    };
    localStorage.setItem(key, JSON.stringify(data));
}

/**
 * Get the last opened chapter for a book
 */
function getLastOpenedChapter(bookId) {
    const key = `last_opened_chapter::${bookId}`;
    const data = localStorage.getItem(key);

    if (data) {
        try {
            return JSON.parse(data);
        } catch (e) {
            return null;
        }
    }

    return null;
}

/**
 * Clear all reading progress for a book
 */
function clearBookProgress(bookId) {
    const keys = Object.keys(localStorage);

    keys.forEach(key => {
        if (key.startsWith(`reading_progress::${bookId}::`) ||
            key.startsWith(`last_opened_chapter::${bookId}`)) {
            localStorage.removeItem(key);
        }
    });
}

/**
 * Get all reading progress for a book
 */
function getBookProgress(bookId) {
    const keys = Object.keys(localStorage);
    const progress = {};

    keys.forEach(key => {
        if (key.startsWith(`reading_progress::${bookId}::`)) {
            const chapterId = key.split('::')[2];
            const data = localStorage.getItem(key);

            if (data) {
                try {
                    progress[chapterId] = JSON.parse(data);
                } catch (e) {
                    // Skip invalid data
                }
            }
        }
    });

    return progress;
}

/**
 * Throttle function for scroll events
 */
function throttle(func, delay) {
    let timeoutId;
    let lastRan;

    return function (...args) {
        const context = this;

        if (!lastRan) {
            func.apply(context, args);
            lastRan = Date.now();
        } else {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(function () {
                if ((Date.now() - lastRan) >= delay) {
                    func.apply(context, args);
                    lastRan = Date.now();
                }
            }, delay - (Date.now() - lastRan));
        }
    };
}

/**
 * Debounce function for scroll events
 */
function debounce(func, delay) {
    let timeoutId;

    return function (...args) {
        const context = this;
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(context, args), delay);
    };
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format date for display
 */
function formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;

    // Less than 1 minute
    if (diff < 60000) {
        return '刚刚';
    }

    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
    }

    // Less than 1 day
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
    }

    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}天前`;
    }

    // Format as date
    return date.toLocaleDateString('zh-CN');
}
