import React, { useState } from 'react';
import { Link } from 'react-router-dom';

const Contact = () => {
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow-lg p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Contact Us</h1>
        <p className="text-gray-600 mb-6">
          Get in touch for a demo or questions about CertiVert.
        </p>

        {submitted ? (
          <div className="py-6 text-center">
            <p className="text-green-600 font-medium mb-2">Thanks for your message!</p>
            <p className="text-gray-600 text-sm">We'll get back to you soon.</p>
            <Link to="/" className="mt-4 inline-block text-indigo-600 hover:underline">Back to Home</Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input type="text" required className="w-full px-4 py-2 border rounded-lg" placeholder="Your name" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" required className="w-full px-4 py-2 border rounded-lg" placeholder="your@email.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
              <textarea rows={4} required className="w-full px-4 py-2 border rounded-lg" placeholder="Your message..." />
            </div>
            <button type="submit" className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700">
              Send Message
            </button>
          </form>
        )}

        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-600">Or email us directly: <a href="mailto:contact@certivert.local" className="text-indigo-600">contact@certivert.local</a></p>
          <Link to="/" className="mt-4 inline-block text-sm text-gray-500 hover:text-gray-700">← Back to Home</Link>
        </div>
      </div>
    </div>
  );
};

export default Contact;
