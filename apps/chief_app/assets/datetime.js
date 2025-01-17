function updateDateTime() {
    const datetimeDisplay = document.getElementById('current-date-output');
    if (datetimeDisplay) {
        const daysOfWeek = ['вс', 'пн', 'вт', 'ср', 'чт', 'пт', 'сб'];
        const currentDate = new Date();
        const dayOfWeek = daysOfWeek[currentDate.getDay()];
        const dayOfMonth = currentDate.getDate();
        const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
        const month = months[currentDate.getMonth()];
        const year = currentDate.getFullYear();
        const hours = String(currentDate.getHours()).padStart(2, '0');
        const minutes = String(currentDate.getMinutes()).padStart(2, '0');
        const seconds = String(currentDate.getSeconds()).padStart(2, '0');

        const formattedDate = `${hours}:${minutes}:${seconds} ${dayOfWeek} ${dayOfMonth} ${month} ${year}`;

        datetimeDisplay.textContent = formattedDate;
    }
}

// Обновляем каждую секунду
setInterval(updateDateTime, 1000);
