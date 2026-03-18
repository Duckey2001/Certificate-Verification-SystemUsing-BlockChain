import React, { useState } from 'react';

const ProfileEditor = ({ user, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    institution: user?.institution || '',
    phone: user?.phone || '',
    user_type: user?.user_type || 'individual',
    bio: user?.bio || ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 animate-scaleIn">
        <div className="px-6 py-4 bg-gradient-to-r from-gray-700 to-gray-800 rounded-t-2xl flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">Edit Profile</h3>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6">
          <div className="flex items-center space-x-4 mb-6">
            <div className="relative">
              <div className="w-20 h-20 rounded-full bg-gradient-to-r from-red-500 to-orange-500 flex items-center justify-center text-white font-bold text-2xl">
                {formData.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <button className="absolute bottom-0 right-0 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-100 border-2 border-gray-200">
                📷
              </button>
            </div>
            <div>
              <p className="text-sm text-gray-500">Profile Picture</p>
              <p className="text-xs text-gray-400">Click the camera to upload</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Username</label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-red-500 focus:ring focus:ring-red-200"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-red-500 focus:ring focus:ring-red-200"
                required
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Institution</label>
            <input
              type="text"
              value={formData.institution}
              onChange={(e) => setFormData({...formData, institution: e.target.value})}
              placeholder="Enter your institution name"
              className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-red-500 focus:ring focus:ring-red-200"
            />
          </div>

          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                placeholder="+266 XXXX XXXX"
                className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-red-500 focus:ring focus:ring-red-200"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">User Type</label>
              <select
                value={formData.user_type}
                onChange={(e) => setFormData({...formData, user_type: e.target.value})}
                className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-red-500 focus:ring focus:ring-red-200"
              >
                <option value="individual">Individual</option>
                <option value="institution">Institution</option>
              </select>
            </div>
          </div>

          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Bio</label>
            <textarea
              value={formData.bio}
              onChange={(e) => setFormData({...formData, bio: e.target.value})}
              rows="3"
              placeholder="Tell us a bit about yourself"
              className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-red-500 focus:ring focus:ring-red-200"
            />
          </div>

          <div className="flex space-x-3 mt-6 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-3 bg-gradient-to-r from-red-500 to-orange-600 rounded-xl text-white font-medium hover:from-red-600 hover:to-orange-700 transition-all transform hover:scale-105"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileEditor;
