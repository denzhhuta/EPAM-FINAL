function openModal(tableNumber) {
  document.getElementById('table-number').textContent = tableNumber;
  document.getElementById('modal').style.display = 'flex';
}

function closeModal() {
  document.getElementById('modal').style.display = 'none';
}

function resetForm() {
  document.getElementById('name').value = "";
  document.getElementById('surname').value = "";
  document.getElementById('email').value = "";
  document.getElementById('phone').value = "";
}

function getBooking() {
  const tableNumber = document.getElementById('table-number').textContent;

  fetch('/get-table-bookings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ tableNumber })
  })
    .then(response => response.json())
    .then(data => {
      // Handle the response data
      if (data.bookings) {
        // Process the bookings
        let message = `Bookings for Table ${tableNumber}:\n`;
        for (const booking of data.bookings) {
          // Access the booking start and end times
          const start = booking.booking_start;
          const end = booking.booking_end;

          // Prepare the booking information message
          message += `\nBooking start: ${start}\nBooking end: ${end}\n`;
        }
        // Display the booking information as an alert
        alert(message);
      } else {
        // No bookings found for the table
        alert(`No bookings found for Table ${tableNumber}`);
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
}


function confirmBooking(event) {
  event.preventDefault();

  const tableNumber = document.getElementById('table-number').textContent;
  const name = document.getElementById('name').value;
  const surname = document.getElementById('surname').value;
  const email = document.getElementById('email').value;
  const phone = document.getElementById('phone').value;
  const startTime = document.getElementById('start-time').value;
  const endTime = document.getElementById('end-time').value;

  const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  const nameRegex = /^[A-Za-z\s]+$/;
  const surnameRegex = /^[A-Za-z\s]+$/;
  const phoneRegex = /^\+\d+$/;

  const isEmailValid = emailRegex.test(email);
  const isNameValid = nameRegex.test(name);
  const isSurnameValid = surnameRegex.test(surname);
  const isPhoneValid = phoneRegex.test(phone);

  const startTimeObj = new Date(startTime);
  const endTimeObj = new Date(endTime);
  const currentTime = new Date();

  if (!startTime || !endTime || startTimeObj <= currentTime || startTimeObj >= endTimeObj) {
    alert('Please select a valid start and end time.');
    return;
  }

  const minBookingTime = 30 * 60 * 1000; // 30 minutes in milliseconds
  const maxBookingTime = 2 * 60 * 60 * 1000; // 2 hours in milliseconds
  const bookingDuration = endTimeObj - startTimeObj;

  if (bookingDuration < minBookingTime || bookingDuration > maxBookingTime) {
    alert('The booking duration should be between 30 minutes and 2 hours.');
    return;
  }

  const bookingStartHours = startTimeObj.getHours()
  const bookingEndHours= endTimeObj.getHours()

  if (bookingStartHours <= 9 && bookingEndHours >= 0) {
    alert('Sorry, but we are closed from 00:00 to 10:00.\nChoose a valid time!')
    return;
  }

  if (isEmailValid && isNameValid && isSurnameValid && isPhoneValid) {
    // Prepare the data to send to the server
    const bookingData = {
      tableNumber,
      name,
      surname,
      email,
      phone,
      startTime,
      endTime
    };

    // Make a POST request to check table availability
    fetch('/check-table-availability', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(bookingData)
    })
      .then(response => response.json())
      .then(data => {
        if (data.available) {
          // Table is available, proceed with booking
          // Make a POST request to book the table
          fetch('/book-table', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(bookingData)
          })
            .then(response => response.json())
            .then(data => {
              // Handle booking response
              if (data.success) {
                alert('Table booked successfully!');
                resetForm();
                closeModal();
                // Add the booked class to the table element
                const tableElement = document.getElementById(`table-${bookingData.tableNumber}`);
                tableElement.classList.add('booked');
              } else {
                alert('Table booking failed. Please try again.');
              }
            })
            .catch(error => {
              console.error('Error:', error);
            });
        } else {
          // Table is not available
          let errorMessage = 'Sorry, the table is already booked. Please choose another table or time slot.';
      
          //alert('Sorry, the table is already booked. Please choose another table or time slot.');

         // Display the overlapping bookings, if available
         if (data.overlappingBookings) {
          const overlappingBookingsMessage = `The table is already booked during the following times:\n${data.overlappingBookings.join('\n')}`;
          errorMessage += '\n' + overlappingBookingsMessage;
        }

        alert(errorMessage);
      }
    })
    .catch(error => {
      console.error('Error:', error);
    });
} else {
  alert('Please enter valid information in all fields.');
}
}