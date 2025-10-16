document.addEventListener('DOMContentLoaded', function() {
    // Fetch provinces from the API
    fetch('https://dev.farizdotid.com/api/daerahindonesia/provinsi')
      .then(response => response.json())
      .then(data => {
        const provinceSelect = document.getElementById('province');
        data.provinsi.forEach(province => {
          const option = document.createElement('option');
          option.value = province.id;
          option.text = province.nama;
          provinceSelect.appendChild(option);
        });
      })
      .catch(error => {
        console.error('Error fetching provinces:', error);
      });
    
    // Add event listener for province change
    document.getElementById('province').addEventListener('change', function() {
      const provinceId = this.value;
      const citySelect = document.getElementById('city');
      citySelect.innerHTML = ''; // Clear city options
      
      // Fetch cities based on selected province
      fetch(`https://dev.farizdotid.com/api/daerahindonesia/kota?id_provinsi=${provinceId}`)
        .then(response => response.json())
        .then(data => {
          data.kota_kabupaten.forEach(city => {
            const option = document.createElement('option');
            option.value = city.id;
            option.text = city.nama;
            citySelect.appendChild(option);
          });
        })
        .catch(error => {
          console.error('Error fetching cities:', error);
        });
    });
  });
  