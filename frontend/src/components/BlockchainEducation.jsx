import React, { useState } from 'react';

const BlockchainEducation = () => {
  const [activeSection, setActiveSection] = useState('basics');

  const sections = [
    {
      id: 'basics',
      title: 'Blockchain Basics',
      icon: '📚',
      content: {
        overview: 'Blockchain is a secure digital ledger that records certificate transactions in a way that makes them tamper-proof.',
        keyPoints: [
          'Each certificate is stored as a unique transaction',
          'Once recorded, certificates cannot be altered',
          'All participants can verify certificate authenticity',
          'No single entity controls the certificate records'
        ],
        analogy: 'Think of it as a digital notary that everyone can trust but no one can change.'
      }
    },
    {
      id: 'certificates',
      title: 'Certificate Storage',
      icon: '📜',
      content: {
        overview: 'Educational certificates are stored on the blockchain as permanent, verifiable records.',
        keyPoints: [
          'Student certificates get a unique digital fingerprint (hash)',
          'The hash is stored on multiple computers worldwide',
          'Anyone can verify if a certificate is authentic',
          'Employers and institutions can trust certificate validity'
        ],
        analogy: 'Like a graduation certificate that can be instantly verified by any university in the world.'
      }
    },
    {
      id: 'verification',
      title: 'Verification Process',
      icon: '✅',
      content: {
        overview: 'Certificate verification happens instantly using blockchain technology.',
        keyPoints: [
          'Scan or enter certificate details',
          'System checks blockchain for matching record',
          'Verification result appears in seconds',
          'No need to contact issuing institution'
        ],
        analogy: 'Like checking if a banknote is real - instant verification without calling the bank.'
      }
    },
    {
      id: 'security',
      title: 'Security Features',
      icon: '🔒',
      content: {
        overview: 'Blockchain provides multiple layers of security for certificate protection.',
        keyPoints: [
          'Cryptographic encryption protects all data',
          'Distributed storage prevents single point failures',
          'Consensus mechanism validates all transactions',
          'Immutable records prevent certificate tampering'
        ],
        analogy: 'Like having thousands of safes worldwide, each containing the same certificate records.'
      }
    },
    {
      id: 'benefits',
      title: 'Benefits',
      icon: '🎯',
      content: {
        overview: 'Blockchain certificates offer significant advantages over traditional paper certificates.',
        keyPoints: [
          'Instant verification saves time and money',
          'Eliminates certificate fraud and forgery',
          'Reduces administrative overhead for institutions',
          'Increases trust in educational credentials'
        ],
        analogy: 'Like upgrading from paper mail to instant messaging - faster, more reliable, and more secure.'
      }
    }
  ];

  const currentSection = sections.find(s => s.id === activeSection);

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6">
        <h2 className="text-2xl font-bold mb-2">Understanding Blockchain for Certificates</h2>
        <p className="text-purple-100">Learn how blockchain technology secures educational certificates</p>
      </div>

      {/* Navigation */}
      <div className="border-b border-gray-200">
        <div className="flex space-x-1 p-4 overflow-x-auto">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors whitespace-nowrap ${
                activeSection === section.id
                  ? 'bg-purple-100 text-purple-700 border-2 border-purple-300'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border-2 border-transparent'
              }`}
            >
              <span className="text-xl">{section.icon}</span>
              <span className="font-medium">{section.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        {currentSection && (
          <div className="space-y-6">
            {/* Overview */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border-l-4 border-purple-500">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                {currentSection.icon} {currentSection.title}
              </h3>
              <p className="text-gray-700 leading-relaxed">
                {currentSection.content.overview}
              </p>
            </div>

            {/* Key Points */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <h4 className="font-semibold text-gray-800 mb-4">Key Points</h4>
              <div className="space-y-3">
                {currentSection.content.keyPoints.map((point, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-purple-600 text-sm font-bold">{index + 1}</span>
                    </div>
                    <p className="text-gray-700">{point}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Analogy */}
            <div className="bg-blue-50 rounded-xl p-6 border-l-4 border-blue-500">
              <h4 className="font-semibold text-blue-800 mb-2">Simple Analogy</h4>
              <p className="text-blue-700 italic">
                "{currentSection.content.analogy}"
              </p>
            </div>

            {/* Interactive Demo for Basics */}
            {activeSection === 'basics' && (
              <div className="bg-gray-50 rounded-xl p-6">
                <h4 className="font-semibold text-gray-800 mb-4">Interactive Demo</h4>
                <div className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-purple-200 rounded-lg flex items-center justify-center">
                      <span className="text-2xl">📄</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">Certificate Created</p>
                      <p className="text-sm text-gray-600">Student certificate is issued</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-blue-200 rounded-lg flex items-center justify-center">
                      <span className="text-2xl">🔐</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">Digital Fingerprint</p>
                      <p className="text-sm text-gray-600">Unique hash is generated</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-green-200 rounded-lg flex items-center justify-center">
                      <span className="text-2xl">⛓️</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">Stored on Blockchain</p>
                      <p className="text-sm text-gray-600">Record is distributed worldwide</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-yellow-200 rounded-lg flex items-center justify-center">
                      <span className="text-2xl">✅</span>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">Instant Verification</p>
                      <p className="text-sm text-gray-600">Anyone can verify authenticity</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Interactive Demo for Verification */}
            {activeSection === 'verification' && (
              <div className="bg-gray-50 rounded-xl p-6">
                <h4 className="font-semibold text-gray-800 mb-4">Try Verification Process</h4>
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Certificate Hash (Sample)
                    </label>
                    <input
                      type="text"
                      defaultValue="0x7d8a9f3e2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg font-mono text-sm"
                      readOnly
                    />
                  </div>
                  
                  <button className="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition-colors">
                    Verify Certificate
                  </button>
                  
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-green-600">✅</span>
                      <span className="font-medium text-green-800">Certificate Verified</span>
                    </div>
                    <p className="text-sm text-green-700 mt-1">
                      This certificate is authentic and stored on the blockchain.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* FAQ Section */}
            <div className="bg-yellow-50 rounded-xl p-6">
              <h4 className="font-semibold text-yellow-800 mb-4">Frequently Asked Questions</h4>
              <div className="space-y-4">
                <div>
                  <p className="font-medium text-gray-800">Is blockchain technology complicated?</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Not for users! The system handles all the complex technology. You just need to scan or enter certificate details.
                  </p>
                </div>
                
                <div>
                  <p className="font-medium text-gray-800">What if I lose my certificate?</p>
                  <p className="text-sm text-gray-600 mt-1">
                    No problem! The blockchain record is permanent. You can get a new copy and verify it anytime.
                  </p>
                </div>
                
                <div>
                  <p className="font-medium text-gray-800">How fast is verification?</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Instant! Most verifications take less than 5 seconds from start to finish.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BlockchainEducation;
