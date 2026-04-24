import React from 'react';

export default function ContactForm({ formData, setFormData, isComplete }) {
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 space-y-4">
      <h3 className="text-lg font-semibold text-gray-800 border-b pb-2">Complainant Details</h3>
      <p className="text-xs text-gray-500 mb-4">
        Please provide your contact information. The chatbot will only ask you for the details of the incident.
      </p>

      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Full Name</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            disabled={isComplete}
            placeholder="John Doe"
            className="w-full text-sm p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              disabled={isComplete}
              placeholder="10-digit number"
              className="w-full text-sm p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              disabled={isComplete}
              placeholder="john@example.com"
              className="w-full text-sm p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Incident Date & Time</label>
          <input
            type="datetime-local"
            name="incident_datetime"
            value={formData.incident_datetime}
            onChange={handleChange}
            disabled={isComplete}
            className="w-full text-sm p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">City / State of Incident</label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            disabled={isComplete}
            placeholder="e.g., Mumbai, Maharashtra"
            className="w-full text-sm p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
          />
        </div>
      </div>
    </div>
  );
}
