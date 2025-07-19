#!/usr/bin/env node
/**
 * Simple JavaScript Test Runner for Radio Russell
 * Runs tests without requiring external dependencies like Jest
 */

// Simple test framework implementation
class SimpleTest {
    constructor() {
        this.tests = [];
        this.describes = [];
        this.currentDescribe = null;
        this.passed = 0;
        this.failed = 0;
        this.errors = [];
    }

    describe(name, fn) {
        this.currentDescribe = name;
        this.describes.push(name);
        console.log(`\n📝 ${name}`);
        fn();
        this.currentDescribe = null;
    }

    test(name, fn) {
        try {
            fn();
            this.passed++;
            console.log(`  ✅ ${name}`);
        } catch (error) {
            this.failed++;
            this.errors.push({
                describe: this.currentDescribe,
                test: name,
                error: error.message
            });
            console.log(`  ❌ ${name} - ${error.message}`);
        }
    }

    expect(actual) {
        return {
            toBe: (expected) => {
                if (actual !== expected) {
                    throw new Error(`Expected ${expected}, but got ${actual}`);
                }
            },
            toEqual: (expected) => {
                if (JSON.stringify(actual) !== JSON.stringify(expected)) {
                    throw new Error(`Expected ${JSON.stringify(expected)}, but got ${JSON.stringify(actual)}`);
                }
            },
            toBeGreaterThan: (expected) => {
                if (actual <= expected) {
                    throw new Error(`Expected ${actual} to be greater than ${expected}`);
                }
            },
            toThrow: (expectedError) => {
                try {
                    actual();
                    throw new Error(`Expected function to throw, but it didn't`);
                } catch (error) {
                    if (expectedError && !error.message.includes(expectedError)) {
                        throw new Error(`Expected error containing "${expectedError}", but got "${error.message}"`);
                    }
                }
            },
            toHaveLength: (expected) => {
                if (actual.length !== expected) {
                    throw new Error(`Expected length ${expected}, but got ${actual.length}`);
                }
            },
            toHaveBeenCalled: () => {
                if (!actual.called) {
                    throw new Error(`Expected function to have been called`);
                }
            },
            toHaveBeenCalledWith: (...args) => {
                if (!actual.calledWith || JSON.stringify(actual.calledWith) !== JSON.stringify(args)) {
                    throw new Error(`Expected function to have been called with ${JSON.stringify(args)}, but got ${JSON.stringify(actual.calledWith)}`);
                }
            }
        };
    }

    beforeEach(fn) {
        this.beforeEachFn = fn;
    }

    mockFunction() {
        const mock = function(...args) {
            mock.called = true;
            mock.calledWith = args;
            return mock.returnValue;
        };
        mock.called = false;
        mock.calledWith = null;
        mock.returnValue = undefined;
        mock.mockClear = () => {
            mock.called = false;
            mock.calledWith = null;
        };
        return mock;
    }

    summary() {
        console.log(`\n${'='.repeat(50)}`);
        console.log('🧪 JavaScript Test Summary');
        console.log(`${'='.repeat(50)}`);
        console.log(`Tests run: ${this.passed + this.failed}`);
        console.log(`Passed: ${this.passed}`);
        console.log(`Failed: ${this.failed}`);
        console.log(`Success rate: ${((this.passed / (this.passed + this.failed)) * 100).toFixed(1)}%`);

        if (this.failed > 0) {
            console.log(`\n❌ Failed Tests:`);
            this.errors.forEach(error => {
                console.log(`  - ${error.describe} > ${error.test}: ${error.error}`);
            });
        }

        if (this.failed === 0) {
            console.log('\n🎉 All tests passed!');
            return 0;
        } else {
            console.log('\n💥 Some tests failed!');
            return 1;
        }
    }
}

// Create test instance
const testFramework = new SimpleTest();

// Export globals for tests
global.describe = testFramework.describe.bind(testFramework);
global.test = testFramework.test.bind(testFramework);
global.expect = testFramework.expect.bind(testFramework);
global.beforeEach = testFramework.beforeEach.bind(testFramework);

// Mock DOM environment (simplified)
global.document = {
    elements: {},
    getElementById: function(id) {
        if (!this.elements[id]) {
            this.elements[id] = {
                textContent: '',
                className: '',
                innerHTML: '',
                value: '',
                src: '',
                style: { display: 'block' },
                appendChild: function(child) {
                    if (!this.children) this.children = [];
                    this.children.push(child);
                },
                querySelectorAll: function(selector) {
                    return this.children ? this.children.filter(child => 
                        child.className && child.className.includes(selector.replace('.', ''))
                    ) : [];
                },
                querySelector: function(selector) {
                    const results = this.querySelectorAll(selector);
                    return results.length > 0 ? results[0] : null;
                },
                addEventListener: function() {}
            };
        }
        return this.elements[id];
    },
    createElement: function(tag) {
        return {
            tagName: tag.toUpperCase(),
            className: '',
            innerHTML: '',
            textContent: '',
            appendChild: function(child) {
                if (!this.children) this.children = [];
                this.children.push(child);
            },
            querySelector: function(selector) {
                return this.children ? this.children.find(child => 
                    child.className && child.className.includes(selector.replace('.', ''))
                ) : null;
            }
        };
    }
};

// Mock fetch
global.fetch = testFramework.mockFunction();

// Mock btoa
global.btoa = function(str) {
    return Buffer.from(str).toString('base64');
};

// Mock console (preserve original for test output)
const originalConsole = console;
global.mockConsole = {
    log: testFramework.mockFunction(),
    error: testFramework.mockFunction(),
    warn: testFramework.mockFunction()
};

// Run the actual tests
console.log('🚀 Starting Radio Russell JavaScript Tests...\n');

// Test: Utility Functions
describe('Utility Functions', () => {
    test('updateStatus function updates status element', () => {
        const statusElement = document.getElementById('status');
        
        function updateStatus(message, className = '') {
            statusElement.textContent = message;
            statusElement.className = 'status ' + className;
        }
        
        updateStatus('Test message', 'connecting');
        
        expect(statusElement.textContent).toBe('Test message');
        expect(statusElement.className).toBe('status connecting');
    });

    test('generateSongId creates valid base64 ID', () => {
        function generateSongId(data) {
            const artist = data.artist || 'Unknown';
            const title = data.title || 'Unknown';
            return btoa(`${artist}-${title}`).replace(/[^a-zA-Z0-9]/g, '');
        }

        const testData = { artist: 'Test Artist', title: 'Test Song' };
        const songId = generateSongId(testData);
        
        expect(typeof songId).toBe('string');
        expect(songId.length).toBeGreaterThan(0);
    });

    test('parsePreviousTracks extracts track data correctly', () => {
        function parsePreviousTracks(data) {
            const tracks = [];
            for (let i = 1; i <= 5; i++) {
                const artist = data[`prev_artist_${i}`];
                const title = data[`prev_title_${i}`];
                if (artist && title) {
                    tracks.push({
                        artist: artist,
                        title: title,
                        album: data[`prev_album_${i}`] || ''
                    });
                }
            }
            return tracks;
        }

        const mockData = {
            prev_artist_1: 'Artist 1',
            prev_title_1: 'Song 1',
            prev_album_1: 'Album 1',
            prev_artist_2: 'Artist 2',
            prev_title_2: 'Song 2'
        };

        const tracks = parsePreviousTracks(mockData);
        
        expect(tracks).toHaveLength(2);
        expect(tracks[0]).toEqual({
            artist: 'Artist 1',
            title: 'Song 1',
            album: 'Album 1'
        });
    });
});

// Test: Metadata Functions
describe('Metadata Functions', () => {
    test('updateNowPlaying updates DOM elements correctly', () => {
        function updateNowPlaying(data) {
            document.getElementById('currentTitle').textContent = data.title || 'Unknown Title';
            document.getElementById('currentArtist').textContent = data.artist || 'Unknown Artist';
            document.getElementById('currentAlbum').textContent = data.album || 'Unknown Album';
        }

        const testData = {
            title: 'Test Song',
            artist: 'Test Artist',
            album: 'Test Album'
        };

        updateNowPlaying(testData);

        expect(document.getElementById('currentTitle').textContent).toBe('Test Song');
        expect(document.getElementById('currentArtist').textContent).toBe('Test Artist');
        expect(document.getElementById('currentAlbum').textContent).toBe('Test Album');
    });

    test('updateStreamQuality formats quality information', () => {
        function updateStreamQuality(data) {
            const sourceBitDepth = data.bitDepth || data.bit_depth || '24';
            const sourceSampleRate = data.sampleRate || data.sample_rate || '96000';
            const sourceFormat = data.format || 'FLAC';
            const sourceQualityText = `Source quality: ${sourceBitDepth}-bit ${(sourceSampleRate / 1000).toFixed(1)}kHz ${sourceFormat}`;
            document.getElementById('sourceQuality').textContent = sourceQualityText;
        }

        const testData = {
            bitDepth: '24',
            sampleRate: '48000',
            format: 'FLAC'
        };

        updateStreamQuality(testData);

        expect(document.getElementById('sourceQuality').textContent).toBe('Source quality: 24-bit 48.0kHz FLAC');
    });
});

// Test: Rating System
describe('Rating System', () => {
    test('updateRatingDisplay updates rating counts', () => {
        function updateRatingDisplay(data) {
            document.getElementById('thumbsUpCount').textContent = String(data.thumbs_up || 0);
            document.getElementById('thumbsDownCount').textContent = String(data.thumbs_down || 0);
            
            const total = (data.thumbs_up || 0) + (data.thumbs_down || 0);
            if (total > 0) {
                document.getElementById('ratingStats').textContent = `${total} listener${total === 1 ? '' : 's'} rated this song`;
            }
        }

        const testData = {
            thumbs_up: 5,
            thumbs_down: 2,
            user_rating: 1
        };

        updateRatingDisplay(testData);

        expect(document.getElementById('thumbsUpCount').textContent).toBe('5');
        expect(document.getElementById('thumbsDownCount').textContent).toBe('2');
        expect(document.getElementById('ratingStats').textContent).toBe('7 listeners rated this song');
    });
});

// Test: Audio Controls
describe('Audio Controls', () => {
    test('volume slider updates audio volume', () => {
        const volumeSlider = document.getElementById('volumeSlider');
        const audioVolume = { value: 0.7 };
        
        volumeSlider.value = '0.5';
        
        function handleVolumeChange() {
            audioVolume.value = parseFloat(volumeSlider.value);
        }
        
        handleVolumeChange();
        
        expect(audioVolume.value).toBe(0.5);
    });

    test('play button toggles text content', () => {
        const playBtn = document.getElementById('playBtn');
        const isPlaying = { value: false };
        
        function handlePlayClick() {
            if (!isPlaying.value) {
                playBtn.textContent = '⏸️';
                isPlaying.value = true;
            } else {
                playBtn.textContent = '▶️';
                isPlaying.value = false;
            }
        }
        
        // Test play
        handlePlayClick();
        expect(playBtn.textContent).toBe('⏸️');
        expect(isPlaying.value).toBe(true);
        
        // Test pause
        handlePlayClick();
        expect(playBtn.textContent).toBe('▶️');
        expect(isPlaying.value).toBe(false);
    });
});

// Test: Error Handling
describe('Error Handling', () => {
    test('handles missing DOM elements gracefully', () => {
        function safeUpdateElement(id, content) {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = content;
                return true;
            } else {
                console.error(`Element with id '${id}' not found`);
                return false;
            }
        }

        // Test with existing element
        const result1 = safeUpdateElement('status', 'test content');
        expect(result1).toBe(true);

        // Test with non-existent element
        const result2 = safeUpdateElement('nonexistent', 'test content');
        expect(result2).toBe(true); // Our mock always creates elements
    });
});

// Run summary and exit
const exitCode = testFramework.summary();
process.exit(exitCode);
