// Fetch and display dashboard data
document.addEventListener("DOMContentLoaded", () => {
    fetchTotalEntries();
    fetchClassEntries();
    fetchMissingInspections();
    fetchNotApproved();
    fetchFailedItems();
  });
  
  // Fetch total entries with vehicle_type W
  function fetchTotalEntries() {
    fetch('/total_entries')
      .then(response => response.json())
      .then(data => {
        document.getElementById('totalEntries').innerText = data.total_entries;
      })
      .catch(err => console.error('Error fetching total entries:', err));
  }
  
  // Fetch entries per class
  function fetchClassEntries() {
    fetch('/class_entries')
      .then(response => response.json())
      .then(data => {
        const list = document.getElementById('classEntries');
        list.innerHTML = ''; // Clear existing list
        data.class_entries.forEach(entry => {
          const li = document.createElement('li');
          li.innerText = `${Object.keys(entry)[0]}: ${Object.values(entry)[0]} entries`;
          list.appendChild(li);
        });
      })
      .catch(err => console.error('Error fetching class entries:', err));
  }
  
  // Fetch total entries without inspection reports
  function fetchMissingInspections() {
    fetch('/missing_inspections')
      .then(response => response.json())
      .then(data => {
        document.getElementById('missingReports').innerText = data.missing_inspections.length;
      })
      .catch(err => console.error('Error fetching missing inspections:', err));
  }
  
  // Fetch total entries not approved to start
  function fetchNotApproved() {
    fetch('/not_approved_to_start')
      .then(response => response.json())
      .then(data => {
        document.getElementById('notApproved').innerText = data.not_approved_to_start_count;
      })
      .catch(err => console.error('Error fetching not approved entries:', err));
  }
  
  // Fetch total failed items
  function fetchFailedItems() {
    fetch('/failed_items')
      .then(response => response.json())
      .then(data => {
        document.getElementById('failedItems').innerText = data.failed_items_count;
      })
      .catch(err => console.error('Error fetching failed items:', err));
  }
  
  // Action Functions (Add more detail as you implement)
  function addEntry() {
    alert("Redirect to Add Entry Form");
  }
  
  function lookupEntry() {
    alert("Redirect to Lookup Entry Page");
  }
  
  function viewOutstandingItems() {
    alert("Redirect to View Outstanding Items");
  }
  
  function viewVehiclesWithoutInspections() {
    alert("Redirect to Vehicles Without Inspections");
  }
  
  function viewNotApprovedVehicles() {
    alert("Redirect to Not Approved Vehicles");
  }
  
  function viewGarageNumbers() {
    alert("Redirect to View Garage Numbers");
  }
  
  function viewVehicleWeights() {
    alert("Redirect to View Vehicle Weights");
  }

  // Function to set all dropdowns to "Pass"
function setAllToPass() {
  // Get all dropdowns on the page
  const dropdowns = document.querySelectorAll('select[name^="status_"]');

  // Loop through each dropdown and set its value to "Pass"
  dropdowns.forEach(dropdown => {
      dropdown.value = "Pass";
  });

  // Optional: Display a confirmation message
  alert("All items have been set to 'Pass'.");
}

// Function to update the Scrutineer's Licence Number based on the selected Scrutineer's Name
function updateLicenceNumber() {
  // Get the selected scrutineer's name dropdown
  const scrutineerNameDropdown = document.getElementById('scrutineer-name-dropdown');
  const selectedOption = scrutineerNameDropdown.options[scrutineerNameDropdown.selectedIndex];

  // Get the corresponding licence number from the data attribute
  const licenceNumber = selectedOption.getAttribute('data-licence-number');

  // Set the licence number dropdown to match the selected scrutineer's licence number
  const scrutineerLicenceDropdown = document.getElementById('scrutineer-licence-dropdown');
  for (let i = 0; i < scrutineerLicenceDropdown.options.length; i++) {
    if (scrutineerLicenceDropdown.options[i].value === licenceNumber) {
      scrutineerLicenceDropdown.selectedIndex = i;
      break;
    }
  }
}
// Fetch total vehicles denied start
function fetchDeniedStart() {
  fetch('/denied_start_count')
    .then(response => response.json())
    .then(data => {
      document.getElementById('deniedStart').innerText = data.denied_start_count;
    })
    .catch(err => console.error('Error fetching denied start count:', err));
}

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', () => {
  fetchDeniedStart();
});
document.addEventListener('DOMContentLoaded', () => {
  // Add event listeners to all status buttons
  const statusButtons = document.querySelectorAll('.status-button');
  statusButtons.forEach(button => {
    button.addEventListener('click', (event) => {
      const itemId = button.getAttribute('data-item-id');
      const status = button.getAttribute('data-status');

      // Update the hidden input field with the new status
      const statusInput = document.getElementById(`status_${itemId}`);
      statusInput.value = status;

      // Update the displayed status
      const statusDisplay = document.getElementById(`status-display-${itemId}`);
      statusDisplay.textContent = status;

      // Optionally, highlight the selected button
      const buttons = button.parentElement.querySelectorAll('.status-button');
      buttons.forEach(btn => btn.classList.remove('selected'));
      button.classList.add('selected');
    });
  });
});