document.querySelectorAll('.camera-feed').forEach((feed) => {
    feed.addEventListener('dblclick', function () {
        this.classList.toggle('fullscreen');
    });
});
