function updateDateTime() {
    const datetimeDisplay = document.getElementById('current-date-output');
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

    const formattedDate = `${dayOfWeek} ${dayOfMonth} ${month} ${year} ${hours}:${minutes}:${seconds}`;

    datetimeDisplay.textContent = formattedDate;
}

// Вызываем функцию обновления с интервалом в 1 секунду
setInterval(updateDateTime, 1000);


